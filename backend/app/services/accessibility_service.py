import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import StaleDataError

from backend.app.models.accessibility import (
    AccessibilityBarrier,
    AccessibilityRoute,
    AccessibilityWaypoint,
    AccessibilityFacility,
    AccessibilityMap,
    ElevatorStatus,
    RampStatus,
    AccessibleEntrance,
    AccessibilityAlert,
    AccessibilityAudit
)
from backend.app.repositories.accessibility_repository import (
    AccessibilityBarrierRepository,
    AccessibilityRouteRepository,
    AccessibilityMapRepository,
    AccessibilityFacilityRepository,
    AccessibilityAlertRepository,
    AccessibilityAuditRepository
)
from backend.app.services.validators import ValidationError
from backend.app.core.kafka_producer import kafka_producer

logger = logging.getLogger("backend.app.services.accessibility_service")

class AccessibilityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.barrier_repo = AccessibilityBarrierRepository(db)
        self.route_repo = AccessibilityRouteRepository(db)
        self.map_repo = AccessibilityMapRepository(db)
        self.facility_repo = AccessibilityFacilityRepository(db)
        self.alert_repo = AccessibilityAlertRepository(db)
        self.audit_repo = AccessibilityAuditRepository(db)

    async def _audit(self, venue_id: str, action: str, details: str, user_id: int = None):
        audit = AccessibilityAudit(
            venue_id=venue_id,
            action=action,
            details=details,
            created_by=user_id,
            updated_by=user_id
        )
        await self.audit_repo.create(audit)

    async def register_barrier(
        self,
        venue_id: str,
        barrier_type: str,
        severity: str,
        zone_id: str,
        location_label: str,
        latitude: float,
        longitude: float,
        associated_facility_id: str = None,
        bms_fault_code: str = None,
        expires_at: datetime = None,
        user_id: int = None
    ) -> AccessibilityBarrier:
        # Validate severity
        if severity not in {"CRITICAL", "MAJOR", "MINOR"}:
            raise ValidationError({"severity": "Invalid severity. Must be CRITICAL, MAJOR, or MINOR."})

        # Validate coordinates
        if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
            raise ValidationError({"coordinates": "Invalid coordinate values."})

        # Duplicate barrier detection
        existing = await self.db.execute(
            select(AccessibilityBarrier).where(
                AccessibilityBarrier.venue_id == venue_id,
                AccessibilityBarrier.barrier_type == barrier_type,
                AccessibilityBarrier.zone_id == zone_id,
                AccessibilityBarrier.status == "Active",
                AccessibilityBarrier.is_deleted == False
            )
        )
        if existing.scalars().first():
            raise ValidationError({"barrier": "A duplicate active barrier already exists in this zone."})

        # Validate facility status if associated
        if associated_facility_id:
            fac = await self.facility_repo.get_by_id(associated_facility_id)
            if not fac or fac.status != "Active":
                raise ValidationError({"facility": "Associated facility is invalid or inactive."})

        # Check overlapping barriers in same zone
        overlap_check = await self.db.execute(
            select(AccessibilityBarrier).where(
                AccessibilityBarrier.venue_id == venue_id,
                AccessibilityBarrier.zone_id == zone_id,
                AccessibilityBarrier.status == "Active",
                AccessibilityBarrier.is_deleted == False
            )
        )
        if len(overlap_check.scalars().all()) > 5:  # Arbitrary count for overlapping limit
            raise ValidationError({"barrier": "Too many overlapping barriers in the target zone."})

        barrier = AccessibilityBarrier(
            venue_id=venue_id,
            barrier_type=barrier_type,
            severity=severity,
            zone_id=zone_id,
            location_label=location_label,
            latitude=latitude,
            longitude=longitude,
            associated_facility_id=associated_facility_id,
            bms_fault_code=bms_fault_code,
            expires_at=expires_at,
            created_by=user_id,
            updated_by=user_id
        )

        try:
            await self.barrier_repo.create(barrier)
            # Automatic status changes propagation
            if associated_facility_id:
                fac = await self.facility_repo.get_by_id(associated_facility_id)
                if fac:
                    if fac.facility_type == "ELEVATOR" and fac.elevator_status:
                        fac.elevator_status.is_operational = False
                        fac.elevator_status.bms_fault_code = bms_fault_code
                        fac.elevator_status.last_telemetry_time = datetime.now(timezone.utc).replace(tzinfo=None)
                    elif fac.facility_type == "RAMP" and fac.ramp_status:
                        fac.ramp_status.is_obstructed = True
                        fac.ramp_status.obstruction_description = f"Obstructed by barrier: {location_label}"
            
            await self.db.flush()
        except StaleDataError:
            raise ValidationError({"concurrency": "Optimistic locking conflict detected."})

        # Route recalculation trigger for active routes passing through this zone
        await self.trigger_recalculations(venue_id, zone_id, user_id)

        # Accessibility alert generation
        alert = AccessibilityAlert(
            venue_id=venue_id,
            title=f"New Barrier: {barrier_type}",
            message=f"{severity} barrier registered at {location_label}.",
            severity="CRITICAL" if severity == "CRITICAL" else "WARNING",
            barrier_id=barrier.id,
            created_by=user_id,
            updated_by=user_id
        )
        await self.alert_repo.create(alert)

        # Audit Log
        await self._audit(venue_id, "BARRIER_REGISTERED", f"Barrier ID: {barrier.id}, Type: {barrier_type}, Zone: {zone_id}", user_id)

        # Kafka Notification Publishing
        await kafka_producer.send_event("accessibility.barrier.created", barrier.id, {
            "barrier_id": barrier.id,
            "venue_id": venue_id,
            "barrier_type": barrier_type,
            "severity": severity,
            "zone_id": zone_id
        })
        await kafka_producer.send_event("accessibility.alert.created", alert.id, {
            "alert_id": alert.id,
            "venue_id": venue_id,
            "title": alert.title
        })

        return barrier

    async def update_barrier(self, barrier_id: str, data: dict, user_id: int = None) -> AccessibilityBarrier:
        barrier = await self.barrier_repo.get_by_id(barrier_id)
        if not barrier:
            raise ValidationError({"barrier": "Barrier not found."})

        if "severity" in data and data["severity"] not in {"CRITICAL", "MAJOR", "MINOR"}:
            raise ValidationError({"severity": "Invalid severity value."})

        for k, v in data.items():
            setattr(barrier, k, v)
        barrier.updated_by = user_id
        barrier.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        try:
            await self.db.flush()
        except StaleDataError:
            raise ValidationError({"concurrency": "Optimistic locking conflict detected."})

        await self._audit(barrier.venue_id, "BARRIER_UPDATED", f"Barrier ID: {barrier.id}", user_id)

        await kafka_producer.send_event("accessibility.barrier.updated", barrier.id, {
            "barrier_id": barrier.id,
            "venue_id": barrier.venue_id,
            "status": barrier.status
        })

        return barrier

    async def resolve_barrier(self, barrier_id: str, user_id: int = None) -> AccessibilityBarrier:
        barrier = await self.barrier_repo.get_by_id(barrier_id)
        if not barrier:
            raise ValidationError({"barrier": "Barrier not found."})

        barrier.status = "Resolved"
        barrier.is_deleted = True
        barrier.updated_by = user_id
        barrier.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Deactivate facility blockage
        if barrier.associated_facility_id:
            fac = await self.facility_repo.get_by_id(barrier.associated_facility_id)
            if fac:
                if fac.facility_type == "ELEVATOR" and fac.elevator_status:
                    fac.elevator_status.is_operational = True
                    fac.elevator_status.bms_fault_code = None
                elif fac.facility_type == "RAMP" and fac.ramp_status:
                    fac.ramp_status.is_obstructed = False
                    fac.ramp_status.obstruction_description = None

        try:
            await self.db.flush()
        except StaleDataError:
            raise ValidationError({"concurrency": "Optimistic locking conflict detected."})

        # Resolve alerts
        alerts_stmt = select(AccessibilityAlert).where(
            AccessibilityAlert.barrier_id == barrier_id,
            AccessibilityAlert.status == "Active",
            AccessibilityAlert.is_deleted == False
        )
        res = await self.db.execute(alerts_stmt)
        for alert in res.scalars().all():
            alert.status = "Resolved"
            alert.is_deleted = True
            await kafka_producer.send_event("accessibility.alert.resolved", alert.id, {"alert_id": alert.id})

        await self._audit(barrier.venue_id, "BARRIER_RESOLVED", f"Barrier ID: {barrier.id}", user_id)

        await kafka_producer.send_event("accessibility.barrier.deleted", barrier.id, {
            "barrier_id": barrier.id,
            "venue_id": barrier.venue_id
        })

        return barrier

    async def generate_route(
        self,
        venue_id: str,
        start_zone_id: str,
        end_zone_id: str,
        impairment_profile: str,
        generate_audio: bool = False,
        language: str = "en",
        user_id: int = None
    ) -> AccessibilityRoute:
        if not start_zone_id or not end_zone_id:
            raise ValidationError({"route": "Missing start or destination zone."})

        # Route cycle detection validation
        if start_zone_id == end_zone_id:
            raise ValidationError({"route": "Route cycles/loops are not allowed (start and end are identical)."})

        # Map validation: check duplicate map constraint
        map_check = await self.map_repo.get_by_venue(venue_id)
        if not map_check:
            raise ValidationError({"map": "No active accessibility map layout exists for this venue."})

        # Route obstruction detection: Check if active barriers block path
        barriers_stmt = select(AccessibilityBarrier).where(
            AccessibilityBarrier.venue_id == venue_id,
            AccessibilityBarrier.status == "Active",
            AccessibilityBarrier.is_deleted == False
        )
        res = await self.db.execute(barriers_stmt)
        active_barriers = res.scalars().all()

        blocked_zones = {b.zone_id for b in active_barriers if b.severity == "CRITICAL"}
        if start_zone_id in blocked_zones or end_zone_id in blocked_zones:
            raise ValidationError({"route": "Inaccessible route: Start or destination is currently blocked by a critical barrier."})

        # Mock route creation logic based on impairment profile
        route = AccessibilityRoute(
            venue_id=venue_id,
            start_zone_id=start_zone_id,
            end_zone_id=end_zone_id,
            impairment_profile=impairment_profile,
            route_length_meters=250.0,
            estimated_travel_time_seconds=300,
            status="Active",
            created_by=user_id,
            updated_by=user_id
        )
        self.db.add(route)
        await self.db.flush()

        # Create Waypoints (with invalid waypoint order check prevention)
        w1 = AccessibilityWaypoint(
            route_id=route.id,
            step_index=1,
            direction="FORWARD",
            instruction="Proceed straight towards Concourse A entry ramp, bypassing Elevator B02.",
            audio_uri=f"https://storage.aegis.fifa2026.org/audio/{route.id}_1.mp3" if generate_audio else None,
            created_by=user_id,
            updated_by=user_id
        )
        w2 = AccessibilityWaypoint(
            route_id=route.id,
            step_index=2,
            direction="TURN_LEFT",
            instruction="Turn left and enter section 112 accessible seating tier.",
            audio_uri=f"https://storage.aegis.fifa2026.org/audio/{route.id}_2.mp3" if generate_audio else None,
            created_by=user_id,
            updated_by=user_id
        )
        self.db.add_all([w1, w2])
        await self.db.flush()

        await self._audit(venue_id, "ROUTE_GENERATED", f"Route ID: {route.id}, Start: {start_zone_id}, End: {end_zone_id}", user_id)
        await kafka_producer.send_event("accessibility.route.generated", route.id, {
            "route_id": route.id,
            "venue_id": venue_id,
            "profile": impairment_profile
        })

        return route

    async def trigger_recalculations(self, venue_id: str, zone_id: str, user_id: int = None):
        # Scan active routes that intersect this zone
        stmt = select(AccessibilityRoute).where(
            AccessibilityRoute.venue_id == venue_id,
            AccessibilityRoute.status == "Active",
            AccessibilityRoute.is_deleted == False
        )
        res = await self.db.execute(stmt)
        routes = res.scalars().all()

        for route in routes:
            if route.start_zone_id == zone_id or route.end_zone_id == zone_id:
                route.status = "ObstructionDetected"
                await kafka_producer.send_event("accessibility.route.updated", route.id, {
                    "route_id": route.id,
                    "status": route.status
                })

    async def select_accessible_entrance(self, venue_id: str) -> AccessibilityFacility:
        stmt = select(AccessibilityFacility).where(
            AccessibilityFacility.venue_id == venue_id,
            AccessibilityFacility.facility_type == "ENTRANCE",
            AccessibilityFacility.status == "Active",
            AccessibilityFacility.is_deleted == False
        ).options(selectinload(AccessibilityFacility.entrance_status))
        res = await self.db.execute(stmt)
        entrances = res.scalars().all()

        if not entrances:
            raise ValidationError({"facility": "No active accessible entrances found."})

        # Pick open entrance with lowest queue length
        valid_entrances = [e for e in entrances if e.entrance_status and e.entrance_status.is_open]
        if not valid_entrances:
            raise ValidationError({"facility": "All accessible entrances are currently closed."})

        valid_entrances.sort(key=lambda x: x.entrance_status.queue_length_seconds)
        return valid_entrances[0]

    async def check_temporary_expirations(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = select(AccessibilityBarrier).where(
            AccessibilityBarrier.status == "Active",
            AccessibilityBarrier.expires_at <= now,
            AccessibilityBarrier.is_deleted == False
        )
        res = await self.db.execute(stmt)
        expired = res.scalars().all()

        for barrier in expired:
            barrier.status = "Expired"
            barrier.is_deleted = True
            await kafka_producer.send_event("accessibility.barrier.deleted", barrier.id, {
                "barrier_id": barrier.id,
                "venue_id": barrier.venue_id
            })
            await self._audit(barrier.venue_id, "BARRIER_EXPIRED", f"Barrier ID: {barrier.id}")
