from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, Tuple, List
from backend.app.models.transit import (
    TransitRoute, TransitStop, TransitVehicle, Driver, Operator,
    TransitHub, ParkingZone, ShuttleService, VehicleAssignment,
    DriverAssignment, TransitSchedule, TransitTrip, TransitTelemetry,
    TransitDelay, TransitCapacity, TransitOccupancy, TransitQueue,
    TransitETA, TransitIncidentLink, TransitAudit, TransitRouteStop,
    TransitAlert
)

class RouteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, route_id: int) -> Optional[TransitRoute]:
        stmt = select(TransitRoute).where(
            TransitRoute.id == route_id,
            TransitRoute.is_deleted == False
        ).options(
            selectinload(TransitRoute.stops_association).selectinload(TransitRouteStop.stop),
            selectinload(TransitRoute.schedules),
            selectinload(TransitRoute.shuttle_services),
            selectinload(TransitRoute.vehicle_assignments)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, route_code: str) -> Optional[TransitRoute]:
        stmt = select(TransitRoute).where(
            TransitRoute.route_code == route_code,
            TransitRoute.is_deleted == False
        ).options(
            selectinload(TransitRoute.stops_association).selectinload(TransitRouteStop.stop)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_routes(
        self,
        limit: int = 50,
        offset: int = 0,
        route_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[TransitRoute], int]:
        stmt = select(TransitRoute).where(TransitRoute.is_deleted == False).order_by(TransitRoute.id)
        if route_type:
            stmt = stmt.where(TransitRoute.route_type == route_type)
        if status:
            stmt = stmt.where(TransitRoute.status == status)
        if search:
            stmt = stmt.where(
                (TransitRoute.name.ilike(f"%{search}%")) |
                (TransitRoute.route_code.ilike(f"%{search}%"))
            )

        # Count query
        count_stmt = select(func.count(TransitRoute.id)).where(TransitRoute.is_deleted == False)
        if route_type:
            count_stmt = count_stmt.where(TransitRoute.route_type == route_type)
        if status:
            count_stmt = count_stmt.where(TransitRoute.status == status)
        if search:
            count_stmt = count_stmt.where(
                (TransitRoute.name.ilike(f"%{search}%")) |
                (TransitRoute.route_code.ilike(f"%{search}%"))
            )

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.limit(limit).offset(offset).options(
            selectinload(TransitRoute.stops_association).selectinload(TransitRouteStop.stop)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def save(self, route: TransitRoute) -> TransitRoute:
        self.db.add(route)
        await self.db.flush()
        return route


class StopRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, stop_id: int) -> Optional[TransitStop]:
        stmt = select(TransitStop).where(
            TransitStop.id == stop_id,
            TransitStop.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, stop_code: str) -> Optional[TransitStop]:
        stmt = select(TransitStop).where(
            TransitStop.stop_code == stop_code,
            TransitStop.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_stops(self, limit: int = 50, offset: int = 0) -> Tuple[List[TransitStop], int]:
        stmt = select(TransitStop).where(TransitStop.is_deleted == False).order_by(TransitStop.id)
        count_stmt = select(func.count(TransitStop.id)).where(TransitStop.is_deleted == False)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def save(self, stop: TransitStop) -> TransitStop:
        self.db.add(stop)
        await self.db.flush()
        return stop


class VehicleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, vehicle_id: int) -> Optional[TransitVehicle]:
        stmt = select(TransitVehicle).where(
            TransitVehicle.id == vehicle_id,
            TransitVehicle.is_deleted == False
        ).options(
            selectinload(TransitVehicle.capacities),
            selectinload(TransitVehicle.vehicle_assignments)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, vehicle_code: str) -> Optional[TransitVehicle]:
        stmt = select(TransitVehicle).where(
            TransitVehicle.vehicle_code == vehicle_code,
            TransitVehicle.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_vehicles(
        self,
        limit: int = 50,
        offset: int = 0,
        vehicle_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[TransitVehicle], int]:
        stmt = select(TransitVehicle).where(TransitVehicle.is_deleted == False).order_by(TransitVehicle.id)
        if vehicle_type:
            stmt = stmt.where(TransitVehicle.vehicle_type == vehicle_type)
        if status:
            stmt = stmt.where(TransitVehicle.status == status)

        count_stmt = select(func.count(TransitVehicle.id)).where(TransitVehicle.is_deleted == False)
        if vehicle_type:
            count_stmt = count_stmt.where(TransitVehicle.vehicle_type == vehicle_type)
        if status:
            count_stmt = count_stmt.where(TransitVehicle.status == status)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def save(self, vehicle: TransitVehicle) -> TransitVehicle:
        self.db.add(vehicle)
        await self.db.flush()
        return vehicle


class DriverRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, driver_id: int) -> Optional[Driver]:
        stmt = select(Driver).where(
            Driver.id == driver_id,
            Driver.is_deleted == False
        ).options(
            selectinload(Driver.driver_assignments)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_license(self, license_number: str) -> Optional[Driver]:
        stmt = select(Driver).where(
            Driver.license_number == license_number,
            Driver.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_drivers(self, limit: int = 50, offset: int = 0) -> Tuple[List[Driver], int]:
        stmt = select(Driver).where(Driver.is_deleted == False).order_by(Driver.id)
        count_stmt = select(func.count(Driver.id)).where(Driver.is_deleted == False)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def save(self, driver: Driver) -> Driver:
        self.db.add(driver)
        await self.db.flush()
        return driver


class TripRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, trip_id: int) -> Optional[TransitTrip]:
        stmt = select(TransitTrip).where(
            TransitTrip.id == trip_id,
            TransitTrip.is_deleted == False
        ).options(
            selectinload(TransitTrip.schedule).selectinload(TransitSchedule.route),
            selectinload(TransitTrip.vehicle),
            selectinload(TransitTrip.driver),
            selectinload(TransitTrip.delays)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_trips(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> Tuple[List[TransitTrip], int]:
        stmt = select(TransitTrip).where(TransitTrip.is_deleted == False).order_by(TransitTrip.id)
        if status:
            stmt = stmt.where(TransitTrip.status == status)

        count_stmt = select(func.count(TransitTrip.id)).where(TransitTrip.is_deleted == False)
        if status:
            count_stmt = count_stmt.where(TransitTrip.status == status)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.limit(limit).offset(offset).options(
            selectinload(TransitTrip.schedule).selectinload(TransitSchedule.route),
            selectinload(TransitTrip.vehicle),
            selectinload(TransitTrip.driver)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def save(self, trip: TransitTrip) -> TransitTrip:
        self.db.add(trip)
        await self.db.flush()
        return trip


class ScheduleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, schedule_id: int) -> Optional[TransitSchedule]:
        stmt = select(TransitSchedule).where(
            TransitSchedule.id == schedule_id,
            TransitSchedule.is_deleted == False
        ).options(
            selectinload(TransitSchedule.route)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_overlaps(self, route_id: int, day_of_week: int, departure_time: str, arrival_time: str) -> List[TransitSchedule]:
        stmt = select(TransitSchedule).where(
            TransitSchedule.route_id == route_id,
            TransitSchedule.day_of_week == day_of_week,
            TransitSchedule.is_deleted == False,
            (TransitSchedule.departure_time < arrival_time) & (TransitSchedule.arrival_time > departure_time)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_schedules(self, limit: int = 50, offset: int = 0, route_id: Optional[int] = None) -> Tuple[List[TransitSchedule], int]:
        stmt = select(TransitSchedule).where(TransitSchedule.is_deleted == False).order_by(TransitSchedule.id)
        if route_id:
            stmt = stmt.where(TransitSchedule.route_id == route_id)

        count_stmt = select(func.count(TransitSchedule.id)).where(TransitSchedule.is_deleted == False)
        if route_id:
            count_stmt = count_stmt.where(TransitSchedule.route_id == route_id)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.limit(limit).offset(offset).options(
            selectinload(TransitSchedule.route)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def save(self, schedule: TransitSchedule) -> TransitSchedule:
        self.db.add(schedule)
        await self.db.flush()
        return schedule


class TelemetryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_by_vehicle(self, vehicle_id: int) -> Optional[TransitTelemetry]:
        stmt = select(TransitTelemetry).where(
            TransitTelemetry.vehicle_id == vehicle_id,
            TransitTelemetry.is_deleted == False
        ).order_by(TransitTelemetry.timestamp.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, telemetry: TransitTelemetry) -> TransitTelemetry:
        self.db.add(telemetry)
        await self.db.flush()
        return telemetry


class CapacityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_vehicle(self, vehicle_id: int) -> Optional[TransitCapacity]:
        stmt = select(TransitCapacity).where(
            TransitCapacity.vehicle_id == vehicle_id,
            TransitCapacity.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, capacity: TransitCapacity) -> TransitCapacity:
        self.db.add(capacity)
        await self.db.flush()
        return capacity


class ParkingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, zone_id: int) -> Optional[ParkingZone]:
        stmt = select(ParkingZone).where(
            ParkingZone.id == zone_id,
            ParkingZone.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[ParkingZone]:
        stmt = select(ParkingZone).where(
            ParkingZone.name == name,
            ParkingZone.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_zones(self, limit: int = 50, offset: int = 0) -> Tuple[List[ParkingZone], int]:
        stmt = select(ParkingZone).where(ParkingZone.is_deleted == False).order_by(ParkingZone.id)
        count_stmt = select(func.count(ParkingZone.id)).where(ParkingZone.is_deleted == False)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def save(self, zone: ParkingZone) -> ParkingZone:
        self.db.add(zone)
        await self.db.flush()
        return zone


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, audit: TransitAudit) -> TransitAudit:
        self.db.add(audit)
        await self.db.flush()
        return audit


class OperatorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, operator_id: int) -> Optional[Operator]:
        stmt = select(Operator).where(Operator.id == operator_id, Operator.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, operator: Operator) -> Operator:
        self.db.add(operator)
        await self.db.flush()
        return operator


class HubRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, hub_id: int) -> Optional[TransitHub]:
        stmt = select(TransitHub).where(TransitHub.id == hub_id, TransitHub.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[TransitHub]:
        stmt = select(TransitHub).where(TransitHub.name == name, TransitHub.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, hub: TransitHub) -> TransitHub:
        self.db.add(hub)
        await self.db.flush()
        return hub


class ShuttleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, shuttle_id: int) -> Optional[ShuttleService]:
        stmt = select(ShuttleService).where(ShuttleService.id == shuttle_id, ShuttleService.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, shuttle: ShuttleService) -> ShuttleService:
        self.db.add(shuttle)
        await self.db.flush()
        return shuttle


class VehicleAssignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, assignment: VehicleAssignment) -> VehicleAssignment:
        self.db.add(assignment)
        await self.db.flush()
        return assignment


class DriverAssignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, assignment: DriverAssignment) -> DriverAssignment:
        self.db.add(assignment)
        await self.db.flush()
        return assignment


class DelayRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, delay: TransitDelay) -> TransitDelay:
        self.db.add(delay)
        await self.db.flush()
        return delay


class OccupancyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, occupancy: TransitOccupancy) -> TransitOccupancy:
        self.db.add(occupancy)
        await self.db.flush()
        return occupancy

    async def get_latest_by_hub(self, hub_name: str) -> Optional[TransitOccupancy]:
        stmt = select(TransitOccupancy).join(TransitStop).where(
            (TransitStop.name == hub_name) | (TransitStop.stop_code == hub_name),
            TransitOccupancy.is_deleted == False
        ).order_by(TransitOccupancy.timestamp.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class QueueRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, queue: TransitQueue) -> TransitQueue:
        self.db.add(queue)
        await self.db.flush()
        return queue


class ETARepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, eta: TransitETA) -> TransitETA:
        self.db.add(eta)
        await self.db.flush()
        return eta


class IncidentLinkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, link: TransitIncidentLink) -> TransitIncidentLink:
        self.db.add(link)
        await self.db.flush()
        return link


class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, alert_id: int) -> Optional[TransitAlert]:
        stmt = select(TransitAlert).where(TransitAlert.id == alert_id, TransitAlert.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, alert_code: str) -> Optional[TransitAlert]:
        stmt = select(TransitAlert).where(TransitAlert.alert_code == alert_code, TransitAlert.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, alert: TransitAlert) -> TransitAlert:
        self.db.add(alert)
        await self.db.flush()
        return alert

