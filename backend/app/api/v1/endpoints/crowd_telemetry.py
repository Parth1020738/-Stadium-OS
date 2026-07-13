from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.crowd_schemas import (
    CrowdSnapshotOut,
    CrowdSnapshotCreate,
    CrowdSnapshotUpdate,
    OccupancyHistoryOut,
    OccupancyCreate,
    DensityMetricsOut,
    DensityMetricsCreate,
    IngressFlowOut,
    IngressFlowCreate,
    EgressFlowOut,
    EgressFlowCreate,
    HeatmapTileOut,
    HeatmapTileCreate,
    CrowdThresholdOut,
    CrowdThresholdCreate,
    CrowdAlertOut
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
from backend.app.repositories.knowledge_repository import AuditLogRepository
from backend.app.services.crowd_service import (
    CrowdSnapshotService,
    CrowdAlertService,
    OccupancyService,
    DensityService,
    FlowMetricsService,
    HeatmapService,
    ThresholdService
)
from backend.app.core.kafka_producer import kafka_producer

router = APIRouter()

@router.post("/snapshots", response_model=CrowdSnapshotOut, status_code=status.HTTP_201_CREATED)
async def register_snapshot(
    payload: CrowdSnapshotCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    zone_repo = CrowdZoneRepository(db)
    snapshot_repo = CrowdSnapshotRepository(db)
    alert_repo = CrowdAlertRepository(db)
    thresh_repo = CrowdThresholdRepository(db)
    audit_repo = AuditLogRepository(db)

    snapshot_service = CrowdSnapshotService(db, snapshot_repo, zone_repo, audit_repo)
    alert_service = CrowdAlertService(db, alert_repo, audit_repo)
    thresh_service = ThresholdService(db, thresh_repo, zone_repo, alert_service, audit_repo)

    snapshot = await snapshot_service.register_snapshot(
        zone_id=payload.zone_id,
        camera_id=payload.camera_id,
        estimated_count=payload.estimated_count,
        density_level=payload.density_level,
        recorded_at=payload.recorded_at,
        actor_id=current_user.get("user_id")
    )

    # Evaluate thresholds based on new snapshot metrics
    await thresh_service.evaluate_thresholds(
        zone_id=payload.zone_id,
        occupancy_count=payload.estimated_count,
        density_level=payload.density_level,
        actor_id=current_user.get("user_id")
    )

    # Emit event
    await kafka_producer.send_event(
        topic="stadium-crowd-snapshots",
        key=str(payload.zone_id),
        value={
            "snapshot_id": snapshot.id,
            "zone_id": payload.zone_id,
            "estimated_count": payload.estimated_count,
            "density_level": payload.density_level
        }
    )

    return snapshot

@router.put("/snapshots/{id}", response_model=CrowdSnapshotOut)
async def update_snapshot(
    id: int,
    payload: CrowdSnapshotUpdate,
    version_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    zone_repo = CrowdZoneRepository(db)
    snapshot_repo = CrowdSnapshotRepository(db)
    audit_repo = AuditLogRepository(db)

    snapshot_service = CrowdSnapshotService(db, snapshot_repo, zone_repo, audit_repo)
    snapshot = await snapshot_service.update_snapshot(
        snapshot_id=id,
        estimated_count=payload.estimated_count,
        density_level=payload.density_level,
        version_id=version_id,
        actor_id=current_user.get("user_id")
    )
    return snapshot

@router.post("/zones/{zone_id}/occupancy", response_model=OccupancyHistoryOut)
async def record_occupancy(
    zone_id: int,
    payload: OccupancyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    zone_repo = CrowdZoneRepository(db)
    occ_repo = OccupancyRepository(db)
    audit_repo = AuditLogRepository(db)

    service = OccupancyService(db, occ_repo, zone_repo, audit_repo)
    history = await service.calculate_occupancy_percentage(
        zone_id=zone_id,
        occupancy_count=payload.occupancy_count,
        actor_id=current_user.get("user_id")
    )

    await kafka_producer.send_event(
        topic="stadium-occupancy-updates",
        key=str(zone_id),
        value={"zone_id": zone_id, "occupancy_count": payload.occupancy_count}
    )

    return history

@router.post("/zones/{zone_id}/density", response_model=DensityMetricsOut)
async def record_density(
    zone_id: int,
    payload: DensityMetricsCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    zone_repo = CrowdZoneRepository(db)
    heatmap_repo = HeatmapRepository(db)
    audit_repo = AuditLogRepository(db)

    service = DensityService(db, heatmap_repo, zone_repo, audit_repo)
    metric = await service.calculate_density_metrics(
        zone_id=zone_id,
        average_density=payload.average_density,
        peak_density=payload.peak_density,
        actor_id=current_user.get("user_id")
    )
    return metric

@router.post("/zones/{zone_id}/ingress", response_model=IngressFlowOut)
async def record_ingress(
    zone_id: int,
    payload: IngressFlowCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    zone_repo = CrowdZoneRepository(db)
    flow_repo = FlowMetricsRepository(db)
    audit_repo = AuditLogRepository(db)

    service = FlowMetricsService(db, flow_repo, zone_repo, audit_repo)
    ingress = await service.calculate_ingress_flow(
        zone_id=zone_id,
        turnstile_id=payload.turnstile_id,
        scan_rate_per_min=payload.scan_rate_per_min,
        actor_id=current_user.get("user_id")
    )
    return ingress

@router.post("/zones/{zone_id}/egress", response_model=EgressFlowOut)
async def record_egress(
    zone_id: int,
    payload: EgressFlowCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    zone_repo = CrowdZoneRepository(db)
    flow_repo = FlowMetricsRepository(db)
    audit_repo = AuditLogRepository(db)

    service = FlowMetricsService(db, flow_repo, zone_repo, audit_repo)
    egress = await service.calculate_egress_flow(
        zone_id=zone_id,
        exit_gate_id=payload.exit_gate_id,
        flow_velocity=payload.flow_velocity,
        dispersal_rate_per_min=payload.dispersal_rate_per_min,
        actor_id=current_user.get("user_id")
    )
    return egress

@router.post("/zones/{zone_id}/heatmap", response_model=List[HeatmapTileOut])
async def generate_heatmap(
    zone_id: int,
    payload: List[HeatmapTileCreate],
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    zone_repo = CrowdZoneRepository(db)
    heatmap_repo = HeatmapRepository(db)
    audit_repo = AuditLogRepository(db)

    service = HeatmapService(db, heatmap_repo, zone_repo, audit_repo)
    tiles_data = [{"x": t.x, "y": t.y, "val": t.val} for t in payload]
    tiles = await service.generate_heatmap_tiles(
        zone_id=zone_id,
        tiles_data=tiles_data,
        actor_id=current_user.get("user_id")
    )
    return tiles

@router.post("/zones/{zone_id}/thresholds", response_model=CrowdThresholdOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def create_threshold(
    zone_id: int,
    payload: CrowdThresholdCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    zone_repo = CrowdZoneRepository(db)
    thresh_repo = CrowdThresholdRepository(db)
    alert_repo = CrowdAlertRepository(db)
    audit_repo = AuditLogRepository(db)

    alert_service = CrowdAlertService(db, alert_repo, audit_repo)
    service = ThresholdService(db, thresh_repo, zone_repo, alert_service, audit_repo)
    threshold = await service.create_threshold(
        zone_id=zone_id,
        threshold_type=payload.threshold_type,
        value=payload.value,
        actor_id=current_user.get("user_id")
    )
    return threshold

@router.get("/zones/{zone_id}/alerts", response_model=List[CrowdAlertOut])
async def list_active_alerts(
    zone_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    repo = CrowdAlertRepository(db)
    return await repo.get_active_alerts_by_zone(zone_id)

@router.post("/alerts/{id}/resolve", response_model=CrowdAlertOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def resolve_alert(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    alert_repo = CrowdAlertRepository(db)
    audit_repo = AuditLogRepository(db)
    
    service = CrowdAlertService(db, alert_repo, audit_repo)
    alert = await service.resolve_alert(alert_id=id, actor_id=current_user.get("user_id"))
    return alert
