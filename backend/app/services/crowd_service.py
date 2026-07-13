import json
import logging
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.knowledge import AuditLog
from backend.app.repositories.knowledge_repository import AuditLogRepository
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
from backend.app.repositories.crowd_repository import (
    CrowdZoneRepository,
    CrowdSnapshotRepository,
    CrowdAlertRepository,
    HeatmapRepository,
    CrowdThresholdRepository,
    OccupancyRepository,
    FlowMetricsRepository
)
from backend.app.services.crowd_validators import CrowdValidator, CrowdValidationError

logger = logging.getLogger("crowd_service")

class CrowdZoneService:
    def __init__(self, db: AsyncSession, zone_repo: CrowdZoneRepository, threshold_repo: CrowdThresholdRepository, audit_repo: AuditLogRepository):
        self.db = db
        self.zone_repo = zone_repo
        self.threshold_repo = threshold_repo
        self.audit_repo = audit_repo

    async def update_capacity(self, zone_id: int, max_capacity: int, safe_capacity_limit: int, actor_id: int | None = None) -> ZoneCapacity:
        # Check zone exists
        zone = await self.zone_repo.get_zone_by_id(zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        # Validate capacity
        CrowdValidator.validate_zone(zone.name, max_capacity, safe_capacity_limit)

        # Check existing capacity
        stmt = select(ZoneCapacity).where(ZoneCapacity.zone_id == zone_id)
        res = await self.db.execute(stmt)
        capacity = res.scalar_one_or_none()

        if not capacity:
            capacity = ZoneCapacity(zone_id=zone_id, max_capacity=max_capacity, safe_capacity_limit=safe_capacity_limit)
            self.db.add(capacity)
        else:
            capacity.max_capacity = max_capacity
            capacity.safe_capacity_limit = safe_capacity_limit

        await self.db.flush()

        # Audit Log
        audit_entry = AuditLog(
            action="CAPACITY_UPDATE",
            details={"zone_id": zone_id, "max_capacity": max_capacity, "safe_capacity_limit": safe_capacity_limit},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "CAPACITY_UPDATE",
            "zone_id": zone_id,
            "max_capacity": max_capacity,
            "safe_capacity_limit": safe_capacity_limit,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return capacity


class CrowdSnapshotService:
    def __init__(self, db: AsyncSession, repo: CrowdSnapshotRepository, zone_repo: CrowdZoneRepository, audit_repo: AuditLogRepository):
        self.db = db
        self.repo = repo
        self.zone_repo = zone_repo
        self.audit_repo = audit_repo

    async def register_snapshot(self, zone_id: int, camera_id: int | None, estimated_count: int, density_level: float, recorded_at: datetime | None = None, actor_id: int | None = None) -> CrowdSnapshot:
        # Check zone exists
        zone = await self.zone_repo.get_zone_by_id(zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        # Validate density
        CrowdValidator.validate_density(density_level)
        if estimated_count < 0:
            raise CrowdValidationError({"estimated_count": "Estimated count cannot be negative"})

        # Validate camera if reference passed
        if camera_id is not None:
            stmt = select(Camera).where(Camera.id == camera_id, Camera.is_deleted == False)
            res = await self.db.execute(stmt)
            camera = res.scalar_one_or_none()
            if not camera:
                raise HTTPException(status_code=404, detail="Camera not found")

        # Prevent duplicate snapshots at exact same timestamp
        rec_time = recorded_at or datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = select(CrowdSnapshot).where(
            CrowdSnapshot.zone_id == zone_id,
            CrowdSnapshot.camera_id == camera_id,
            CrowdSnapshot.recorded_at == rec_time
        )
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Snapshot at this timestamp already exists for this camera/zone")

        snapshot = CrowdSnapshot(
            zone_id=zone_id,
            camera_id=camera_id,
            estimated_count=estimated_count,
            density_level=density_level,
            recorded_at=rec_time
        )
        await self.repo.create_snapshot(snapshot)

        # Audit Log
        audit_entry = AuditLog(
            action="SNAPSHOT_CREATE",
            details={"zone_id": zone_id, "camera_id": camera_id, "estimated_count": estimated_count},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "SNAPSHOT_CREATE",
            "zone_id": zone_id,
            "camera_id": camera_id,
            "estimated_count": estimated_count,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return snapshot

    async def update_snapshot(self, snapshot_id: int, estimated_count: int, density_level: float, version_id: int, actor_id: int | None = None) -> CrowdSnapshot:
        # Load snapshot
        stmt = select(CrowdSnapshot).where(CrowdSnapshot.id == snapshot_id)
        res = await self.db.execute(stmt)
        snapshot = res.scalar_one_or_none()
        if not snapshot:
            raise HTTPException(status_code=404, detail="Snapshot not found")

        # Validate
        CrowdValidator.validate_density(density_level)
        if estimated_count < 0:
            raise CrowdValidationError({"estimated_count": "Estimated count cannot be negative"})

        # Load parent CrowdZone to check version_id (native optimistic locking)
        zone = await self.zone_repo.get_zone_by_id(snapshot.zone_id)
        if zone.version_id != version_id:
            raise HTTPException(status_code=409, detail="Conflict: Stale version ID. The resource was modified.")

        snapshot.estimated_count = estimated_count
        snapshot.density_level = density_level

        # Increment zone version to trigger locking
        zone.version_id += 1

        try:
            await self.db.flush()
        except StaleDataError:
            raise HTTPException(status_code=409, detail="Conflict: Stale version ID. The resource was modified.")

        # Audit Log
        audit_entry = AuditLog(
            action="SNAPSHOT_UPDATE",
            details={"snapshot_id": snapshot_id, "estimated_count": estimated_count, "density_level": density_level},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "SNAPSHOT_UPDATE",
            "snapshot_id": snapshot_id,
            "estimated_count": estimated_count,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return snapshot


class CrowdAlertService:
    def __init__(self, db: AsyncSession, repo: CrowdAlertRepository, audit_repo: AuditLogRepository):
        self.db = db
        self.repo = repo
        self.audit_repo = audit_repo

    async def generate_alert(self, zone_id: int, alert_type: str, severity: str, message: str, actor_id: int | None = None) -> CrowdAlert:
        if severity not in {"Info", "Warning", "Critical"}:
            raise CrowdValidationError({"severity": "Invalid alert severity"})

        alert = CrowdAlert(
            zone_id=zone_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            triggered_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.repo.create_alert(alert)

        # Audit Log
        audit_entry = AuditLog(
            action="ALERT_GENERATE",
            details={"zone_id": zone_id, "alert_type": alert_type, "severity": severity},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "ALERT_GENERATE",
            "zone_id": zone_id,
            "alert_type": alert_type,
            "severity": severity,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return alert

    async def acknowledge_alert(self, alert_id: int, actor_id: int | None = None) -> None:
        stmt = select(CrowdAlert).where(CrowdAlert.id == alert_id)
        res = await self.db.execute(stmt)
        alert = res.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        # Audit Log
        audit_entry = AuditLog(
            action="ALERT_ACKNOWLEDGE",
            details={"alert_id": alert_id},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "ALERT_ACKNOWLEDGE",
            "alert_id": alert_id,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

    async def resolve_alert(self, alert_id: int, actor_id: int | None = None) -> CrowdAlert:
        stmt = select(CrowdAlert).where(CrowdAlert.id == alert_id)
        res = await self.db.execute(stmt)
        alert = res.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        alert.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.flush()

        # Audit Log
        audit_entry = AuditLog(
            action="ALERT_RESOLVE",
            details={"alert_id": alert_id},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "ALERT_RESOLVE",
            "alert_id": alert_id,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return alert


class OccupancyService:
    def __init__(self, db: AsyncSession, repo: OccupancyRepository, zone_repo: CrowdZoneRepository, audit_repo: AuditLogRepository):
        self.db = db
        self.repo = repo
        self.zone_repo = zone_repo
        self.audit_repo = audit_repo

    async def calculate_occupancy_percentage(self, zone_id: int, occupancy_count: int, actor_id: int | None = None) -> OccupancyHistory:
        zone = await self.zone_repo.get_zone_by_id(zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        stmt = select(ZoneCapacity).where(ZoneCapacity.zone_id == zone_id)
        res = await self.db.execute(stmt)
        capacity = res.scalar_one_or_none()
        if not capacity or capacity.max_capacity <= 0:
            raise HTTPException(status_code=400, detail="Capacity limits not set for this zone")

        util_ratio = float(occupancy_count) / capacity.max_capacity
        CrowdValidator.validate_occupancy(occupancy_count, util_ratio)

        history = OccupancyHistory(
            zone_id=zone_id,
            occupancy_count=occupancy_count,
            capacity_utilization_ratio=util_ratio,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.repo.record_occupancy(history)

        # Audit Log
        audit_entry = AuditLog(
            action="OCCUPANCY_CALCULATE",
            details={"zone_id": zone_id, "occupancy_count": occupancy_count, "utilization_ratio": util_ratio},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "OCCUPANCY_CALCULATE",
            "zone_id": zone_id,
            "occupancy_count": occupancy_count,
            "utilization_ratio": util_ratio,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return history


class DensityService:
    def __init__(self, db: AsyncSession, repo: HeatmapRepository, zone_repo: CrowdZoneRepository, audit_repo: AuditLogRepository):
        self.db = db
        self.repo = repo
        self.zone_repo = zone_repo
        self.audit_repo = audit_repo

    async def calculate_density_metrics(self, zone_id: int, average_density: float, peak_density: float, actor_id: int | None = None) -> DensityMetrics:
        zone = await self.zone_repo.get_zone_by_id(zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        CrowdValidator.validate_density(average_density)
        CrowdValidator.validate_density(peak_density)

        metric = DensityMetrics(
            zone_id=zone_id,
            average_density=average_density,
            peak_density=peak_density,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.repo.record_density_metrics(metric)

        # Audit Log
        audit_entry = AuditLog(
            action="DENSITY_CALCULATE",
            details={"zone_id": zone_id, "average_density": average_density, "peak_density": peak_density},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "DENSITY_CALCULATE",
            "zone_id": zone_id,
            "average_density": average_density,
            "peak_density": peak_density,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return metric


class FlowMetricsService:
    def __init__(self, db: AsyncSession, repo: FlowMetricsRepository, zone_repo: CrowdZoneRepository, audit_repo: AuditLogRepository):
        self.db = db
        self.repo = repo
        self.zone_repo = zone_repo
        self.audit_repo = audit_repo

    async def calculate_ingress_flow(self, zone_id: int, turnstile_id: str, scan_rate_per_min: int, actor_id: int | None = None) -> IngressFlow:
        zone = await self.zone_repo.get_zone_by_id(zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        if scan_rate_per_min < 0:
            raise CrowdValidationError({"scan_rate_per_min": "Scan rate cannot be negative"})

        ingress = IngressFlow(
            zone_id=zone_id,
            turnstile_id=turnstile_id,
            scan_rate_per_min=scan_rate_per_min,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.repo.record_ingress_flow(ingress)

        # Audit Log
        audit_entry = AuditLog(
            action="FLOW_INGRESS_CALCULATE",
            details={"zone_id": zone_id, "turnstile_id": turnstile_id, "scan_rate_per_min": scan_rate_per_min},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "FLOW_INGRESS_CALCULATE",
            "zone_id": zone_id,
            "turnstile_id": turnstile_id,
            "scan_rate_per_min": scan_rate_per_min,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return ingress

    async def calculate_egress_flow(self, zone_id: int, exit_gate_id: str, flow_velocity: float, dispersal_rate_per_min: int, actor_id: int | None = None) -> EgressFlow:
        zone = await self.zone_repo.get_zone_by_id(zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        if flow_velocity < 0.0 or dispersal_rate_per_min < 0:
            raise CrowdValidationError({"flow_velocity": "Values cannot be negative"})

        egress = EgressFlow(
            zone_id=zone_id,
            exit_gate_id=exit_gate_id,
            flow_velocity=flow_velocity,
            dispersal_rate_per_min=dispersal_rate_per_min,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.repo.record_egress_flow(egress)

        # Audit Log
        audit_entry = AuditLog(
            action="FLOW_EGRESS_CALCULATE",
            details={"zone_id": zone_id, "exit_gate_id": exit_gate_id, "flow_velocity": flow_velocity, "dispersal_rate_per_min": dispersal_rate_per_min},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "FLOW_EGRESS_CALCULATE",
            "zone_id": zone_id,
            "exit_gate_id": exit_gate_id,
            "flow_velocity": flow_velocity,
            "dispersal_rate_per_min": dispersal_rate_per_min,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return egress


class HeatmapService:
    def __init__(self, db: AsyncSession, repo: HeatmapRepository, zone_repo: CrowdZoneRepository, audit_repo: AuditLogRepository):
        self.db = db
        self.repo = repo
        self.zone_repo = zone_repo
        self.audit_repo = audit_repo

    async def generate_heatmap_tiles(self, zone_id: int, tiles_data: list[dict], actor_id: int | None = None) -> list[HeatmapTile]:
        zone = await self.zone_repo.get_zone_by_id(zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        tiles = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for tile in tiles_data:
            x, y, val = tile.get("x"), tile.get("y"), tile.get("val")
            if x < 0 or y < 0 or val < 0.0:
                raise CrowdValidationError({"coordinates": "Coordinates and density value cannot be negative"})
            tiles.append(HeatmapTile(
                zone_id=zone_id,
                x_coord=x,
                y_coord=y,
                density_val=val,
                timestamp=now
            ))

        await self.repo.record_heatmap_tiles(tiles)

        # Audit Log
        audit_entry = AuditLog(
            action="HEATMAP_GENERATE",
            details={"zone_id": zone_id, "tile_count": len(tiles)},
            user_id=actor_id,
            timestamp=now
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "HEATMAP_GENERATE",
            "zone_id": zone_id,
            "tile_count": len(tiles),
            "actor_id": actor_id,
            "timestamp": now.isoformat() + "Z"
        }))

        return tiles


class ThresholdService:
    def __init__(self, db: AsyncSession, repo: CrowdThresholdRepository, zone_repo: CrowdZoneRepository, alert_service: CrowdAlertService, audit_repo: AuditLogRepository):
        self.db = db
        self.repo = repo
        self.zone_repo = zone_repo
        self.alert_service = alert_service
        self.audit_repo = audit_repo

    async def create_threshold(self, zone_id: int, threshold_type: str, value: float, actor_id: int | None = None) -> CrowdThreshold:
        zone = await self.zone_repo.get_zone_by_id(zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        CrowdValidator.validate_threshold(threshold_type, value)

        threshold = CrowdThreshold(
            zone_id=zone_id,
            threshold_type=threshold_type,
            value=value,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.repo.create_threshold(threshold)

        # Audit Log
        audit_entry = AuditLog(
            action="THRESHOLD_UPDATE",
            details={"zone_id": zone_id, "threshold_type": threshold_type, "value": value},
            user_id=actor_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        logger.info(json.dumps({
            "event": "THRESHOLD_UPDATE",
            "zone_id": zone_id,
            "threshold_type": threshold_type,
            "value": value,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return threshold

    async def evaluate_thresholds(self, zone_id: int, occupancy_count: int, density_level: float, actor_id: int | None = None) -> list[CrowdAlert]:
        zone = await self.zone_repo.get_zone_by_id(zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")
        await self.db.refresh(zone, ["thresholds"])

        alerts = []
        for t in zone.thresholds:
            if t.threshold_type == "OccupancyWarning" and occupancy_count > t.value:
                # Escalation logic: check if there's also critical threshold
                critical_val = next((x.value for x in zone.thresholds if x.threshold_type == "OccupancyCritical"), None)
                severity = "Critical" if (critical_val and occupancy_count > critical_val) else "Warning"
                
                alert = await self.alert_service.generate_alert(
                    zone_id=zone_id,
                    alert_type="OccupancyAlert",
                    severity=severity,
                    message=f"Occupancy {occupancy_count} exceeded warning threshold {t.value}",
                    actor_id=actor_id
                )
                alerts.append(alert)
                
            elif t.threshold_type == "DensityCritical" and density_level > t.value:
                alert = await self.alert_service.generate_alert(
                    zone_id=zone_id,
                    alert_type="DensityAlert",
                    severity="Critical",
                    message=f"Density level {density_level} exceeded critical threshold {t.value}",
                    actor_id=actor_id
                )
                alerts.append(alert)

        return alerts


class CameraHealthService:
    def __init__(self, db: AsyncSession, zone_repo: CrowdZoneRepository, snapshot_repo: CrowdSnapshotRepository, alert_service: CrowdAlertService, audit_repo: AuditLogRepository):
        self.db = db
        self.zone_repo = zone_repo
        self.snapshot_repo = snapshot_repo
        self.alert_service = alert_service
        self.audit_repo = audit_repo

    async def update_camera_health(self, camera_id: int, connectivity_status: str, latency_ms: int | None, fps: float | None, actor_id: int | None = None) -> CameraHealth:
        stmt = select(Camera).where(Camera.id == camera_id, Camera.is_deleted == False)
        res = await self.db.execute(stmt)
        camera = res.scalar_one_or_none()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")

        if connectivity_status not in {"Connected", "Disconnected"}:
            raise CrowdValidationError({"connectivity_status": "Invalid connectivity status"})

        # Record health log
        health = CameraHealth(
            camera_id=camera_id,
            connectivity_status=connectivity_status,
            latency_ms=latency_ms,
            fps=fps,
            recorded_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.snapshot_repo.record_camera_health(health)

        # Update Camera status
        old_status = camera.status
        new_status = "Active" if connectivity_status == "Connected" else "Offline"
        
        if old_status != new_status:
            camera.status = new_status
            
            # Audit log camera status change
            audit_entry = AuditLog(
                action="CAMERA_STATUS_CHANGE",
                details={"camera_id": camera_id, "old_status": old_status, "new_status": new_status},
                user_id=actor_id,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            await self.audit_repo.create(audit_entry)
            
            logger.info(json.dumps({
                "event": "CAMERA_STATUS_CHANGE",
                "camera_id": camera_id,
                "old_status": old_status,
                "new_status": new_status,
                "actor_id": actor_id,
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
            }))

            # Trigger CameraOffline Alert if camera went offline
            if new_status == "Offline" and camera.zone_id:
                await self.alert_service.generate_alert(
                    zone_id=camera.zone_id,
                    alert_type="CameraOffline",
                    severity="Warning",
                    message=f"Camera {camera.device_id} went offline",
                    actor_id=actor_id
                )

        await self.db.flush()
        await self.db.commit()
        return health
