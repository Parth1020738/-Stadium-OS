from sqlalchemy import select, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.crowd import (
    CrowdZone,
    Camera,
    CameraHealth,
    CrowdSnapshot,
    OccupancyHistory,
    CrowdAlert,
    IngressFlow,
    EgressFlow,
    DensityMetrics,
    HeatmapTile,
    CrowdThreshold,
    ZoneCapacity
)

class CrowdZoneRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_zone_by_id(self, zone_id: int) -> CrowdZone | None:
        stmt = select(CrowdZone).where(
            CrowdZone.id == zone_id,
            CrowdZone.is_deleted == False
        ).options(
            selectinload(CrowdZone.cameras),
            selectinload(CrowdZone.thresholds),
            selectinload(CrowdZone.capacities)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create_zone(self, zone: CrowdZone) -> CrowdZone:
        self.db.add(zone)
        await self.db.flush()
        return zone

    async def get_camera_by_device_id(self, device_id: str) -> Camera | None:
        stmt = select(Camera).where(
            Camera.device_id == device_id,
            Camera.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create_camera(self, camera: Camera) -> Camera:
        self.db.add(camera)
        await self.db.flush()
        return camera


class CrowdSnapshotRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_snapshot(self, snapshot: CrowdSnapshot) -> CrowdSnapshot:
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def get_snapshots_by_zone(self, zone_id: int, limit: int = 50) -> list[CrowdSnapshot]:
        stmt = select(CrowdSnapshot).where(
            CrowdSnapshot.zone_id == zone_id
        ).order_by(desc(CrowdSnapshot.recorded_at)).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def record_camera_health(self, health: CameraHealth) -> CameraHealth:
        self.db.add(health)
        await self.db.flush()
        return health


class CrowdAlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert(self, alert: CrowdAlert) -> CrowdAlert:
        self.db.add(alert)
        await self.db.flush()
        return alert

    async def get_active_alerts_by_zone(self, zone_id: int) -> list[CrowdAlert]:
        stmt = select(CrowdAlert).where(
            CrowdAlert.zone_id == zone_id,
            CrowdAlert.resolved_at == None
        ).order_by(desc(CrowdAlert.triggered_at))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class HeatmapRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_heatmap_tiles(self, tiles: list[HeatmapTile]) -> list[HeatmapTile]:
        self.db.add_all(tiles)
        await self.db.flush()
        return tiles

    async def get_heatmap_by_zone(self, zone_id: int, timestamp=None) -> list[HeatmapTile]:
        stmt = select(HeatmapTile).where(HeatmapTile.zone_id == zone_id)
        if timestamp:
            stmt = stmt.where(HeatmapTile.timestamp == timestamp)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def record_density_metrics(self, metric: DensityMetrics) -> DensityMetrics:
        self.db.add(metric)
        await self.db.flush()
        return metric


class CrowdThresholdRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_threshold(self, threshold: CrowdThreshold) -> CrowdThreshold:
        self.db.add(threshold)
        await self.db.flush()
        return threshold

    async def create_capacity(self, capacity: ZoneCapacity) -> ZoneCapacity:
        self.db.add(capacity)
        await self.db.flush()
        return capacity


class OccupancyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_occupancy(self, history: OccupancyHistory) -> OccupancyHistory:
        self.db.add(history)
        await self.db.flush()
        return history

    async def get_occupancy_history(self, zone_id: int, limit: int = 100) -> list[OccupancyHistory]:
        stmt = select(OccupancyHistory).where(
            OccupancyHistory.zone_id == zone_id
        ).order_by(desc(OccupancyHistory.timestamp)).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class FlowMetricsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_ingress_flow(self, ingress: IngressFlow) -> IngressFlow:
        self.db.add(ingress)
        await self.db.flush()
        return ingress

    async def record_egress_flow(self, egress: EgressFlow) -> EgressFlow:
        self.db.add(egress)
        await self.db.flush()
        return egress
