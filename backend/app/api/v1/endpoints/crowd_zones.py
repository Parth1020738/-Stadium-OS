from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.crowd_schemas import (
    CrowdZoneOut,
    CrowdZoneCreate,
    CrowdZoneUpdate,
    ZoneCapacityOut,
    ZoneCapacityCreate
)
from backend.app.models.crowd import CrowdZone
from backend.app.repositories.crowd_repository import CrowdZoneRepository, CrowdThresholdRepository
from backend.app.repositories.knowledge_repository import AuditLogRepository
from backend.app.services.crowd_service import CrowdZoneService
from backend.app.core.kafka_producer import kafka_producer

router = APIRouter()

@router.get("/", response_model=List[CrowdZoneOut])
async def list_zones(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    stmt = select(CrowdZone).where(CrowdZone.is_deleted == False).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.post("/", response_model=CrowdZoneOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def create_zone(
    payload: CrowdZoneCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    repo = CrowdZoneRepository(db)
    
    # Check duplicate name
    stmt = select(CrowdZone).where(CrowdZone.name == payload.name.strip(), CrowdZone.is_deleted == False)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Zone name already exists")

    zone = CrowdZone(name=payload.name.strip(), description=payload.description)
    await repo.create_zone(zone)
    await db.commit()
    
    # Reload with empty relations to match Out schema structure
    zone_loaded = await repo.get_zone_by_id(zone.id)
    return zone_loaded

@router.get("/{id}", response_model=CrowdZoneOut)
async def get_zone(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    repo = CrowdZoneRepository(db)
    zone = await repo.get_zone_by_id(id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone

@router.put("/{id}", response_model=CrowdZoneOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def update_zone(
    id: int,
    payload: CrowdZoneUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    repo = CrowdZoneRepository(db)
    zone = await repo.get_zone_by_id(id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    if payload.name is not None:
        stmt = select(CrowdZone).where(CrowdZone.name == payload.name.strip(), CrowdZone.id != id, CrowdZone.is_deleted == False)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Zone name already exists")
        zone.name = payload.name.strip()

    if payload.description is not None:
        zone.description = payload.description

    await db.commit()
    return await repo.get_zone_by_id(id)

@router.post("/{id}/capacity", response_model=ZoneCapacityOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def update_zone_capacity(
    id: int,
    payload: ZoneCapacityCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    zone_repo = CrowdZoneRepository(db)
    thresh_repo = CrowdThresholdRepository(db)
    audit_repo = AuditLogRepository(db)
    
    service = CrowdZoneService(db, zone_repo, thresh_repo, audit_repo)
    capacity = await service.update_capacity(
        zone_id=id,
        max_capacity=payload.max_capacity,
        safe_capacity_limit=payload.safe_capacity_limit,
        actor_id=current_user.get("user_id")
    )
    
    # Emit Kafka Event
    await kafka_producer.send_event(
        topic="stadium-crowd-capacity-updates",
        key=str(id),
        value={
            "zone_id": id,
            "max_capacity": payload.max_capacity,
            "safe_capacity_limit": payload.safe_capacity_limit,
            "actor_id": current_user.get("user_id")
        }
    )
    
    return capacity
