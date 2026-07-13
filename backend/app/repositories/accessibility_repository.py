from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
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

class AccessibilityBarrierRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, barrier_id: str) -> AccessibilityBarrier | None:
        stmt = select(AccessibilityBarrier).where(
            AccessibilityBarrier.id == barrier_id,
            AccessibilityBarrier.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_venue(self, venue_id: str, limit: int | None = None, offset: int | None = None) -> list[AccessibilityBarrier]:
        stmt = select(AccessibilityBarrier).where(
            AccessibilityBarrier.venue_id == venue_id,
            AccessibilityBarrier.is_deleted == False
        )
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, barrier: AccessibilityBarrier) -> AccessibilityBarrier:
        self.db.add(barrier)
        await self.db.flush()
        return barrier


class AccessibilityRouteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, route_id: str) -> AccessibilityRoute | None:
        stmt = select(AccessibilityRoute).where(
            AccessibilityRoute.id == route_id,
            AccessibilityRoute.is_deleted == False
        ).options(selectinload(AccessibilityRoute.waypoints))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_venue(self, venue_id: str) -> list[AccessibilityRoute]:
        stmt = select(AccessibilityRoute).where(
            AccessibilityRoute.venue_id == venue_id,
            AccessibilityRoute.is_deleted == False
        ).options(selectinload(AccessibilityRoute.waypoints))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, route: AccessibilityRoute) -> AccessibilityRoute:
        self.db.add(route)
        await self.db.flush()
        return route


class AccessibilityMapRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_venue(self, venue_id: str) -> AccessibilityMap | None:
        stmt = select(AccessibilityMap).where(
            AccessibilityMap.venue_id == venue_id,
            AccessibilityMap.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, acc_map: AccessibilityMap) -> AccessibilityMap:
        self.db.add(acc_map)
        await self.db.flush()
        return acc_map


class AccessibilityFacilityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, facility_id: str) -> AccessibilityFacility | None:
        stmt = select(AccessibilityFacility).where(
            AccessibilityFacility.id == facility_id,
            AccessibilityFacility.is_deleted == False
        ).options(
            selectinload(AccessibilityFacility.elevator_status),
            selectinload(AccessibilityFacility.ramp_status),
            selectinload(AccessibilityFacility.entrance_status)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_venue(self, venue_id: str) -> list[AccessibilityFacility]:
        stmt = select(AccessibilityFacility).where(
            AccessibilityFacility.venue_id == venue_id,
            AccessibilityFacility.is_deleted == False
        ).options(
            selectinload(AccessibilityFacility.elevator_status),
            selectinload(AccessibilityFacility.ramp_status),
            selectinload(AccessibilityFacility.entrance_status)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, facility: AccessibilityFacility) -> AccessibilityFacility:
        self.db.add(facility)
        await self.db.flush()
        return facility


class AccessibilityAlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, alert_id: str) -> AccessibilityAlert | None:
        stmt = select(AccessibilityAlert).where(
            AccessibilityAlert.id == alert_id,
            AccessibilityAlert.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_venue(self, venue_id: str, limit: int | None = None, offset: int | None = None) -> list[AccessibilityAlert]:
        stmt = select(AccessibilityAlert).where(
            AccessibilityAlert.venue_id == venue_id,
            AccessibilityAlert.is_deleted == False
        )
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, alert: AccessibilityAlert) -> AccessibilityAlert:
        self.db.add(alert)
        await self.db.flush()
        return alert


class AccessibilityAuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_venue(self, venue_id: str) -> list[AccessibilityAudit]:
        stmt = select(AccessibilityAudit).where(
            AccessibilityAudit.venue_id == venue_id,
            AccessibilityAudit.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, audit: AccessibilityAudit) -> AccessibilityAudit:
        self.db.add(audit)
        await self.db.flush()
        return audit
