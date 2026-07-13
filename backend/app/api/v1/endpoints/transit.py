from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timezone

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.transit_schemas import (
    TransitRouteResponse, TransitStopResponse, TransitVehicleResponse,
    DriverResponse, ParkingZoneResponse, TransitPaginationResponse,
    TransitStatisticsResponse, TransitAlertRequest, TransitAlertResponseEnvelope,
    TransitEgressPacingRequest, TransitEgressPacingResponseEnvelope,
    CreateRouteRequest, CreateVehicleRequest, AssignVehicleRequest,
    AssignDriverRequest, CreateScheduleRequest, RecordTelemetryRequest,
    TransitScheduleResponse, VehicleAssignmentResponse, DriverAssignmentResponse,
    TransitTelemetryResponse, ParkingZoneResponse
)
from backend.app.services.transit_service import (
    RouteService, VehicleService, DriverService, ScheduleService,
    AssignmentService, TelemetryService, CapacityService, ParkingService,
    TransitService
)
from backend.app.services.validators import ValidationError

router = APIRouter(prefix="/transit", tags=["Transit"])

# Security roles & scopes check helpers
staff_or_admin = RoleChecker(["Staff", "Admin"])
volunteer_or_staff = RoleChecker(["Volunteer", "Staff", "Admin"])

class ScopeChecker:
    def __init__(self, required_scopes: list[str]):
        self.required_scopes = required_scopes

    def __call__(self, user: dict = Depends(get_current_user)) -> dict:
        user_scopes = user.get("scopes", [])
        if isinstance(user_scopes, str):
            user_scopes = user_scopes.split()
        user_roles = user.get("roles", [])
        # Allow Admin bypass (Preserve Admin capabilities)
        if "Admin" in user_roles:
            return user
        if not any(scope in self.required_scopes for scope in user_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Insufficient scope permissions"
            )
        return user

transit_read = ScopeChecker(["transit:read"])
transit_write = ScopeChecker(["transit:write"])
transit_pacing = ScopeChecker(["transit:pacing"])

def get_user_id_from_current_user(current_user: dict) -> int:
    sub = current_user.get("sub")
    if sub and str(sub).isdigit():
        return int(sub)
    u_id = current_user.get("user_id")
    if u_id:
        return int(u_id)
    if sub:
        try:
            return int(sub)
        except ValueError:
            return 9999
    return 9999


# --- Endpoints Defined in 07_API_SPECIFICATION.md ---

@router.get(
    "/routes",
    response_model=TransitPaginationResponse,
    summary="Retrieve route status and timetable metrics"
)
async def list_transit_routes(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    route_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(transit_read)
):
    service = RouteService(db)
    routes, total = await service.repo.list_routes(
        limit=limit,
        offset=offset,
        route_type=route_type,
        status=status,
        search=search
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": routes
    }


@router.get(
    "/hubs/{hub_id}/occupancy",
    response_model=dict,
    summary="Retrieve passenger density values at transit hubs"
)
async def get_hub_occupancy(
    hub_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(transit_read)
):
    service = TransitService(db)
    res = await service.get_hub_occupancy(hub_id)
    return res


@router.post(
    "/alerts",
    response_model=TransitAlertResponseEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Publish service delays or transit emergency alerts"
)
async def ingest_transit_alert(
    req: TransitAlertRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(transit_write)
):
    actor_id = get_user_id_from_current_user(current_user)
    service = TransitService(db)
    start_time = datetime.now(timezone.utc)
    try:
        data = await service.ingest_alert(
            route_id=req.data.route_id,
            hub_id=req.data.hub_id,
            alert_type=req.data.alert_type,
            severity=req.data.severity,
            delay_minutes=req.data.delay_minutes,
            reason=req.data.reason,
            estimated_resolution_time=req.data.estimated_resolution_time,
            actor_id=actor_id,
            correlation_id=req.correlationId
        )
        duration = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        return {
            "traceId": req.traceId,
            "correlationId": req.correlationId,
            "serverTimestamp": datetime.now(timezone.utc),
            "executionDurationMs": max(1, duration),
            "metadata": {},
            "data": data,
            "error": None
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/egress-pacing",
    response_model=TransitEgressPacingResponseEnvelope,
    summary="Update stadium turnstile egress pacing limits"
)
async def apply_egress_pacing(
    req: TransitEgressPacingRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(transit_pacing)
):
    actor_id = get_user_id_from_current_user(current_user)
    service = TransitService(db)
    start_time = datetime.now(timezone.utc)
    try:
        data = await service.apply_egress_pacing(
            venue_id=req.data.venue_id,
            gate_ids=req.data.gate_ids,
            pacing_rate_limit_per_minute=req.data.pacing_rate_limit_per_minute,
            calculation_model=req.data.calculation_model,
            authorized_user_id=req.data.authorized_user_id,
            actor_id=actor_id,
            correlation_id=req.correlationId
        )
        duration = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        return {
            "traceId": req.traceId,
            "correlationId": req.correlationId,
            "serverTimestamp": datetime.now(timezone.utc),
            "executionDurationMs": max(1, duration),
            "metadata": {},
            "data": data,
            "error": None
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


# --- Additional CRUD & Operational Endpoints for Phase 8 ---

@router.post(
    "/routes",
    response_model=TransitRouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new route"
)
async def create_route(
    req: CreateRouteRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    service = RouteService(db)
    try:
        route = await service.create_route(
            name=req.name,
            route_code=req.route_code,
            route_type=req.route_type,
            description=req.description,
            actor_id=actor_id
        )
        return route
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/vehicles",
    response_model=TransitVehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new vehicle"
)
async def create_vehicle(
    req: CreateVehicleRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    service = VehicleService(db)
    try:
        vehicle = await service.create_vehicle(
            vehicle_code=req.vehicle_code,
            license_plate=req.license_plate,
            vehicle_type=req.vehicle_type,
            capacity=req.capacity,
            actor_id=actor_id
        )
        return vehicle
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/assignments/vehicle",
    response_model=VehicleAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a vehicle to a route"
)
async def assign_vehicle(
    req: AssignVehicleRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    service = AssignmentService(db)
    try:
        assignment = await service.assign_vehicle(
            vehicle_id=req.vehicle_id,
            route_id=req.route_id,
            actor_id=actor_id
        )
        return assignment
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/assignments/driver",
    response_model=DriverAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a driver to a vehicle"
)
async def assign_driver(
    req: AssignDriverRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    service = AssignmentService(db)
    try:
        assignment = await service.assign_driver(
            driver_id=req.driver_id,
            vehicle_id=req.vehicle_id,
            actor_id=actor_id
        )
        return assignment
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/schedules",
    response_model=TransitScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new route schedule"
)
async def create_schedule(
    req: CreateScheduleRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    service = ScheduleService(db)
    try:
        sched = await service.create_schedule(
            route_id=req.route_id,
            day_of_week=req.day_of_week,
            departure_time=req.departure_time,
            arrival_time=req.arrival_time,
            actor_id=actor_id
        )
        return sched
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/vehicles/{vehicleId}/telemetry",
    response_model=TransitTelemetryResponse,
    summary="Record vehicle GPS telemetry"
)
async def record_telemetry(
    vehicleId: int,
    req: RecordTelemetryRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(volunteer_or_staff)
):
    actor_id = get_user_id_from_current_user(current_user)
    service = TelemetryService(db)
    telemetry = await service.record_telemetry(
        vehicle_id=vehicleId,
        latitude=req.latitude,
        longitude=req.longitude,
        speed=req.speed,
        heading=req.heading,
        actor_id=actor_id
    )
    return telemetry


@router.get(
    "/statistics",
    response_model=TransitStatisticsResponse,
    summary="Get route operational statistics"
)
async def get_transit_statistics(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    service = TransitService(db)
    stats = await service.get_statistics()
    return stats
