from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.crowd_schemas import (
    CameraOut,
    CameraCreate,
    CameraUpdate,
    CameraHealthOut,
    CameraHealthCreate
)
from backend.app.models.crowd import Camera, CrowdZone
from backend.app.repositories.crowd_repository import CrowdZoneRepository, CrowdSnapshotRepository, CrowdAlertRepository
from backend.app.repositories.knowledge_repository import AuditLogRepository
from backend.app.services.crowd_service import CrowdAlertService, CameraHealthService
from backend.app.core.kafka_producer import kafka_producer

router = APIRouter()

@router.get("/", response_model=List[CameraOut])
async def list_cameras(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    stmt = select(Camera).where(Camera.is_deleted == False).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.post("/", response_model=CameraOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def register_camera(
    payload: CameraCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    repo = CrowdZoneRepository(db)

    # Check unique device_id
    stmt = select(Camera).where(Camera.device_id == payload.device_id.strip(), Camera.is_deleted == False)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Camera device_id already exists")

    # Check zone exists
    if payload.zone_id is not None:
        zone = await repo.get_zone_by_id(payload.zone_id)
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

    camera = Camera(
        device_id=payload.device_id.strip(),
        name=payload.name.strip(),
        zone_id=payload.zone_id,
        status=payload.status or "Active",
        ip_address=payload.ip_address
    )
    await repo.create_camera(camera)
    await db.commit()

    # Reload fresh record
    stmt = select(Camera).where(Camera.id == camera.id)
    res = await db.execute(stmt)
    return res.scalar_one()

@router.get("/{id}", response_model=CameraOut)
async def get_camera(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    stmt = select(Camera).where(Camera.id == id, Camera.is_deleted == False)
    res = await db.execute(stmt)
    camera = res.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera

@router.put("/{id}", response_model=CameraOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def update_camera(
    id: int,
    payload: CameraUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    stmt = select(Camera).where(Camera.id == id, Camera.is_deleted == False)
    res = await db.execute(stmt)
    camera = res.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    if payload.zone_id is not None:
        zone_stmt = select(CrowdZone).where(CrowdZone.id == payload.zone_id, CrowdZone.is_deleted == False)
        zone_res = await db.execute(zone_stmt)
        if not zone_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Zone not found")
        camera.zone_id = payload.zone_id

    if payload.name is not None:
        camera.name = payload.name.strip()
    if payload.status is not None:
        camera.status = payload.status
    if payload.ip_address is not None:
        camera.ip_address = payload.ip_address

    await db.commit()
    
    stmt = select(Camera).where(Camera.id == id)
    res = await db.execute(stmt)
    return res.scalar_one()

@router.post("/{id}/health", response_model=CameraHealthOut)
async def update_camera_health(
    id: int,
    payload: CameraHealthCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    zone_repo = CrowdZoneRepository(db)
    snapshot_repo = CrowdSnapshotRepository(db)
    alert_repo = CrowdAlertRepository(db)
    audit_repo = AuditLogRepository(db)

    alert_service = CrowdAlertService(db, alert_repo, audit_repo)
    service = CameraHealthService(db, zone_repo, snapshot_repo, alert_service, audit_repo)
    
    health = await service.update_camera_health(
        camera_id=id,
        connectivity_status=payload.connectivity_status,
        latency_ms=payload.latency_ms,
        fps=payload.fps,
        actor_id=current_user.get("user_id")
    )

    # Emit Kafka Event
    await kafka_producer.send_event(
        topic="stadium-camera-health-logs",
        key=str(id),
        value={
            "camera_id": id,
            "connectivity_status": payload.connectivity_status,
            "latency_ms": payload.latency_ms,
            "fps": payload.fps
        }
    )

    return health
