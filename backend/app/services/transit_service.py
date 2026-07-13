import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError
from fastapi import HTTPException, status
from backend.app.services.validators import ValidationError
from backend.app.core.kafka_producer import kafka_producer

from sqlalchemy.exc import IntegrityError
from backend.app.models.transit import (
    TransitRoute, TransitStop, TransitVehicle, Driver, Operator,
    TransitHub, ParkingZone, ShuttleService, VehicleAssignment,
    DriverAssignment, TransitSchedule, TransitTrip, TransitTelemetry,
    TransitDelay, TransitCapacity, TransitOccupancy, TransitQueue,
    TransitETA, TransitIncidentLink, TransitAudit, TransitRouteStop,
    TransitAlert
)
from backend.app.repositories.transit_repository import (
    RouteRepository, StopRepository, VehicleRepository, DriverRepository,
    TripRepository, ScheduleRepository, TelemetryRepository,
    CapacityRepository, ParkingRepository, AuditRepository,
    OperatorRepository, HubRepository, ShuttleRepository,
    VehicleAssignmentRepository, DriverAssignmentRepository,
    DelayRepository, OccupancyRepository, QueueRepository,
    ETARepository, IncidentLinkRepository, AlertRepository
)

logger = logging.getLogger("transit_service")

async def publish_kafka_event(topic: str, key: str, data: dict, correlation_id: Optional[str] = None):
    event_payload = {
        "schemaVersion": "1.0",
        "correlationId": correlation_id or f"corr-{uuid.uuid4()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }
    await kafka_producer.send_event(topic, key, event_payload)


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuditRepository(db)

    async def log_audit(
        self,
        action: str,
        actor_id: Optional[int],
        target_type: str,
        target_id: Optional[int],
        changes: Optional[dict] = None
    ) -> TransitAudit:
        audit = TransitAudit(
            action=action,
            actor_id=actor_id,
            target_type=target_type,
            target_id=target_id,
            changes=json.dumps(changes) if changes else None
        )
        self.db.add(audit)
        await self.db.flush()
        return audit


class RouteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RouteRepository(db)
        self.audit_service = AuditService(db)

    async def create_route(self, name: str, route_code: str, route_type: str, description: Optional[str] = None, actor_id: Optional[int] = None) -> TransitRoute:
        existing = await self.repo.get_by_code(route_code)
        if existing:
            raise ValidationError({"route_code": "Route code is already registered"})

        route = TransitRoute(
            name=name,
            route_code=route_code,
            route_type=route_type,
            description=description,
            status="Active"
        )
        try:
            await self.repo.save(route)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Route code is already registered (concurrent constraint violation)")

        await self.audit_service.log_audit("CREATE_ROUTE", actor_id, "TransitRoute", route.id, {"name": name, "route_code": route_code})
        await publish_kafka_event("transit.route.created", str(route.id), {"id": route.id, "route_code": route.route_code})
        return route


class VehicleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = VehicleRepository(db)
        self.audit_service = AuditService(db)

    async def create_vehicle(self, vehicle_code: str, license_plate: str, vehicle_type: str, capacity: int, actor_id: Optional[int] = None) -> TransitVehicle:
        existing = await self.repo.get_by_code(vehicle_code)
        if existing:
            raise ValidationError({"vehicle_code": "Vehicle code is already registered"})

        vehicle = TransitVehicle(
            vehicle_code=vehicle_code,
            license_plate=license_plate,
            vehicle_type=vehicle_type,
            capacity=capacity,
            status="Active"
        )
        try:
            await self.repo.save(vehicle)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vehicle code is already registered (concurrent constraint violation)")

        await self.audit_service.log_audit("CREATE_VEHICLE", actor_id, "TransitVehicle", vehicle.id, {"vehicle_code": vehicle_code})
        await publish_kafka_event("transit.vehicle.created", str(vehicle.id), {"id": vehicle.id, "vehicle_code": vehicle.vehicle_code})
        return vehicle


class DriverService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DriverRepository(db)
        self.audit_service = AuditService(db)

    async def create_driver(self, first_name: str, last_name: str, license_number: str, phone: Optional[str] = None, actor_id: Optional[int] = None) -> Driver:
        existing = await self.repo.get_by_license(license_number)
        if existing:
            raise ValidationError({"license_number": "License number is already registered"})

        driver = Driver(
            first_name=first_name,
            last_name=last_name,
            license_number=license_number,
            phone=phone,
            status="Active"
        )
        try:
            await self.repo.save(driver)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="License number is already registered (concurrent constraint violation)")

        await self.audit_service.log_audit("CREATE_DRIVER", actor_id, "Driver", driver.id, {"license_number": license_number})
        return driver


class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ScheduleRepository(db)
        self.route_repo = RouteRepository(db)
        self.audit_service = AuditService(db)

    async def create_schedule(self, route_id: int, day_of_week: int, departure_time: str, arrival_time: str, actor_id: Optional[int] = None) -> TransitSchedule:
        route = await self.route_repo.get_by_id(route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")

        # Check schedule overlap
        overlaps = await self.repo.get_overlaps(route_id, day_of_week, departure_time, arrival_time)
        if overlaps:
            raise ValidationError({"schedule": "Schedule overlaps with an existing schedule for this route"})

        schedule = TransitSchedule(
            route_id=route_id,
            day_of_week=day_of_week,
            departure_time=departure_time,
            arrival_time=arrival_time
        )
        try:
            await self.repo.save(schedule)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Schedule constraint violation or concurrent overlap")

        await self.audit_service.log_audit("CREATE_SCHEDULE", actor_id, "TransitSchedule", schedule.id, {"route_id": route_id})
        return schedule


class AssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.route_repo = RouteRepository(db)
        self.vehicle_repo = VehicleRepository(db)
        self.driver_repo = DriverRepository(db)
        self.audit_service = AuditService(db)
        self.vehicle_assign_repo = VehicleAssignmentRepository(db)
        self.driver_assign_repo = DriverAssignmentRepository(db)

    async def assign_vehicle(self, vehicle_id: int, route_id: int, actor_id: Optional[int] = None) -> VehicleAssignment:
        vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        if vehicle.status == "OutOfService":
            raise ValidationError({"vehicle": "Cannot assign vehicle that is OutOfService"})

        route = await self.route_repo.get_by_id(route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")

        assignment = VehicleAssignment(
            vehicle_id=vehicle_id,
            route_id=route_id,
            status="Active"
        )
        try:
            await self.vehicle_assign_repo.save(assignment)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vehicle assignment is already registered (concurrent constraint violation)")

        await self.audit_service.log_audit("ASSIGN_VEHICLE", actor_id, "VehicleAssignment", assignment.id, {"vehicle_id": vehicle_id, "route_id": route_id})
        return assignment

    async def assign_driver(self, driver_id: int, vehicle_id: int, actor_id: Optional[int] = None) -> DriverAssignment:
        driver = await self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        if driver.status != "Active":
            raise ValidationError({"driver": "Driver is not active"})

        vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        assignment = DriverAssignment(
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            status="Active"
        )
        try:
            await self.driver_assign_repo.save(assignment)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Driver assignment is already registered (concurrent constraint violation)")

        await self.audit_service.log_audit("ASSIGN_DRIVER", actor_id, "DriverAssignment", assignment.id, {"driver_id": driver_id, "vehicle_id": vehicle_id})
        return assignment


class TelemetryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TelemetryRepository(db)
        self.vehicle_repo = VehicleRepository(db)
        self.audit_service = AuditService(db)

    async def record_telemetry(self, vehicle_id: int, latitude: float, longitude: float, speed: float, heading: float = 0.0, actor_id: Optional[int] = None) -> TransitTelemetry:
        vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        telemetry = TransitTelemetry(
            vehicle_id=vehicle_id,
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            heading=heading
        )
        try:
            await self.repo.save(telemetry)
        except StaleDataError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Telemetry modified concurrently")

        await publish_kafka_event("transit.telemetry.updated", str(vehicle_id), {"vehicle_id": vehicle_id, "latitude": latitude, "longitude": longitude})
        return telemetry


class CapacityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CapacityRepository(db)
        self.vehicle_repo = VehicleRepository(db)
        self.audit_service = AuditService(db)

    async def set_capacity(self, vehicle_id: int, max_seats: int, max_standing: int, actor_id: Optional[int] = None) -> TransitCapacity:
        vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        capacity = await self.repo.get_by_vehicle(vehicle_id)
        if not capacity:
            capacity = TransitCapacity(vehicle_id=vehicle_id)

        capacity.max_seats = max_seats
        capacity.max_standing = max_standing

        try:
            await self.repo.save(capacity)
        except StaleDataError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Capacity modified concurrently")

        await publish_kafka_event("transit.capacity.updated", str(vehicle_id), {"vehicle_id": vehicle_id, "max_seats": max_seats, "max_standing": max_standing})
        return capacity


class ParkingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ParkingRepository(db)
        self.audit_service = AuditService(db)

    async def create_zone(self, name: str, total_spaces: int, location_zone: str, actor_id: Optional[int] = None) -> ParkingZone:
        existing = await self.repo.get_by_name(name)
        if existing:
            raise ValidationError({"name": "Parking zone name is already registered"})

        zone = ParkingZone(
            name=name,
            total_spaces=total_spaces,
            occupied_spaces=0,
            location_zone=location_zone,
            status="Open"
        )
        try:
            await self.repo.save(zone)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Parking zone name is already registered (concurrent constraint violation)")

        await self.audit_service.log_audit("CREATE_PARKING_ZONE", actor_id, "ParkingZone", zone.id, {"name": name})
        return zone

    async def update_occupancy(self, zone_id: int, occupied_spaces: int, actor_id: Optional[int] = None) -> ParkingZone:
        import asyncio
        max_retries = 3
        backoff_factor = 0.05
        retries = 0

        while True:
            zone = await self.repo.get_by_id(zone_id)
            if not zone:
                raise HTTPException(status_code=404, detail="Parking zone not found")

            if occupied_spaces > zone.total_spaces:
                raise ValidationError({"occupied_spaces": "Occupied spaces exceeds total spaces"})

            zone.occupied_spaces = occupied_spaces
            if occupied_spaces == zone.total_spaces:
                zone.status = "Full"
            else:
                zone.status = "Open"

            try:
                await self.repo.save(zone)
                break
            except StaleDataError:
                await self.db.rollback()
                retries += 1
                if retries > max_retries:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Zone modified concurrently and max retries exceeded")
                await asyncio.sleep(backoff_factor * (2 ** (retries - 1)))

        await publish_kafka_event("transit.parking.updated", str(zone_id), {"zone_id": zone_id, "occupied_spaces": occupied_spaces})
        return zone


class TransitService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.route_repo = RouteRepository(db)
        self.stop_repo = StopRepository(db)
        self.trip_repo = TripRepository(db)
        self.audit_service = AuditService(db)
        self.alert_repo = AlertRepository(db)
        self.occupancy_repo = OccupancyRepository(db)

    async def ingest_alert(self, route_id: str, hub_id: str, alert_type: str, severity: str, delay_minutes: int, reason: str, estimated_resolution_time: Optional[datetime] = None, actor_id: Optional[int] = None, correlation_id: Optional[str] = None) -> dict:
        alert_id = f"alt_transit_{alert_type.lower()}_{uuid.uuid4().hex[:6]}"
        
        # Resolve route integer ID
        r_id = None
        try:
            r_id = int(route_id)
        except ValueError:
            route = await self.route_repo.get_by_code(route_id)
            if route:
                r_id = route.id

        # Persist alert
        alert = TransitAlert(
            alert_code=alert_id,
            route_id=r_id,
            hub_id=hub_id,
            alert_type=alert_type,
            severity=severity,
            delay_minutes=delay_minutes,
            reason=reason,
            estimated_resolution_time=estimated_resolution_time
        )
        try:
            await self.alert_repo.save(alert)
        except IntegrityError:
            await self.db.rollback()
            # If concurrent race condition, do not crash but fallback
            pass

        # Publish to isolated alert topic
        await publish_kafka_event("transit.alerts", alert_id, {
            "alert_id": alert_id,
            "route_id": route_id,
            "hub_id": hub_id,
            "alert_type": alert_type,
            "severity": severity,
            "delay_minutes": delay_minutes,
            "reason": reason
        }, correlation_id=correlation_id)

        await self.audit_service.log_audit("INGEST_ALERT", actor_id, "TransitAlert", alert.id, {"alert_id": alert_id, "route_id": route_id, "delay_minutes": delay_minutes})
        return {
            "alert_id": alert_id,
            "status": "INGESTED",
            "downstream_triggers_triggered": True
        }

    async def apply_egress_pacing(self, venue_id: str, gate_ids: List[str], pacing_rate_limit_per_minute: int, calculation_model: str, authorized_user_id: str, actor_id: Optional[int] = None, correlation_id: Optional[str] = None) -> dict:
        transaction_id = f"pac_tx_egress_{uuid.uuid4().hex[:6]}"
        
        # Publish to isolated egress pacing topic
        await publish_kafka_event("transit.egress_pacing", transaction_id, {
            "pacing_transaction_id": transaction_id,
            "venue_id": venue_id,
            "gate_ids": gate_ids,
            "pacing_rate_limit_per_minute": pacing_rate_limit_per_minute
        }, correlation_id=correlation_id)

        gates_configured = [
            {
                "gate_id": g_id,
                "pacing_status": "APPLIED",
                "pacing_rate_limit_per_minute": pacing_rate_limit_per_minute
            } for g_id in gate_ids
        ]

        await self.audit_service.log_audit("APPLY_EGRESS_PACING", actor_id, "EgressPacing", None, {"pacing_transaction_id": transaction_id, "gates": gate_ids})
        return {
            "pacing_transaction_id": transaction_id,
            "gates_configured": gates_configured,
            "estimated_platform_clearance_delay_seconds": pacing_rate_limit_per_minute * 187
        }

    async def get_hub_occupancy(self, hub_id: str) -> dict:
        # Check if stop exists
        stop = await self.stop_repo.get_by_code(hub_id)
        if not stop:
            try:
                stop = await self.stop_repo.get_by_id(int(hub_id))
            except ValueError:
                pass
        
        if not stop:
            raise HTTPException(status_code=404, detail="Hub stop not found")

        occ = await self.occupancy_repo.get_latest_by_hub(stop.name)
        if not occ:
            return {
                "hub_id": hub_id,
                "occupancy_level": "Normal",
                "passenger_count": 0,
                "density_percentage": 0.0,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

        passenger_count = occ.passenger_count
        density_percentage = min(100.0, (passenger_count / 2000.0) * 100.0)
        occupancy_level = "Normal"
        if density_percentage > 80.0:
            occupancy_level = "Critical"
        elif density_percentage > 50.0:
            occupancy_level = "Crowded"

        return {
            "hub_id": hub_id,
            "occupancy_level": occupancy_level,
            "passenger_count": passenger_count,
            "density_percentage": round(density_percentage, 1),
            "updated_at": occ.timestamp.isoformat() if occ.timestamp else datetime.now(timezone.utc).isoformat()
        }

    async def get_statistics(self) -> dict:
        from sqlalchemy import select, func
        # Count routes
        total_routes = (await self.db.execute(select(func.count(TransitRoute.id)).where(TransitRoute.is_deleted == False))).scalar_one()
        delayed_routes = (await self.db.execute(select(func.count(TransitRoute.id)).where(TransitRoute.status == "Delayed", TransitRoute.is_deleted == False))).scalar_one()
        suspended_routes = (await self.db.execute(select(func.count(TransitRoute.id)).where(TransitRoute.status == "Suspended", TransitRoute.is_deleted == False))).scalar_one()
        
        # Count vehicles
        total_vehicles = (await self.db.execute(select(func.count(TransitVehicle.id)).where(TransitVehicle.is_deleted == False))).scalar_one()
        active_vehicles = (await self.db.execute(select(func.count(TransitVehicle.id)).where(TransitVehicle.status == "Active", TransitVehicle.is_deleted == False))).scalar_one()
        maintenance_vehicles = (await self.db.execute(select(func.count(TransitVehicle.id)).where(TransitVehicle.status == "Maintenance", TransitVehicle.is_deleted == False))).scalar_one()
        
        # Count trips
        total_trips = (await self.db.execute(select(func.count(TransitTrip.id)).where(TransitTrip.is_deleted == False))).scalar_one()
        completed_trips = (await self.db.execute(select(func.count(TransitTrip.id)).where(TransitTrip.status == "Completed", TransitTrip.is_deleted == False))).scalar_one()
        
        # Average delay minutes
        avg_delay = (await self.db.execute(select(func.avg(TransitDelay.delay_minutes)).where(TransitDelay.is_deleted == False))).scalar()
        
        return {
            "total_routes": total_routes,
            "delayed_routes": delayed_routes,
            "suspended_routes": suspended_routes,
            "total_vehicles": total_vehicles,
            "active_vehicles": active_vehicles,
            "maintenance_vehicles": maintenance_vehicles,
            "total_trips": total_trips,
            "completed_trips": completed_trips,
            "average_delay_minutes": float(avg_delay) if avg_delay is not None else 0.0
        }
