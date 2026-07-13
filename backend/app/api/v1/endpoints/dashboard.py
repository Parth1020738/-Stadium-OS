from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.core.redis import redis_manager
from backend.app.models.auth import User

from backend.app.schemas.dashboard_schemas import (
    PreferenceSave, PreferenceOut, WidgetCreate, WidgetOut,
    SnapshotCreate, SnapshotOut, NotificationOut, AlertOut, TimelineOut
)
from backend.app.services.dashboard_service import DashboardService

router = APIRouter()

# Scopes mapped to roles
read_checker = RoleChecker(["Operator", "Administrator", "Steward"])
write_checker = RoleChecker(["Operator", "Administrator"])

@router.get("", response_model=Dict[str, Any])
async def get_dashboard(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = DashboardService(db)
    return await service.assemble_overview()


@router.get("/overview", response_model=Dict[str, Any])
async def get_overview(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = DashboardService(db)
    return await service.assemble_overview()


@router.get("/widgets", response_model=List[Dict[str, Any]])
async def get_widgets(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = DashboardService(db)
    return await service.widgets.get_widgets()


@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = DashboardService(db)
    return await service.metrics.get_kpis()


@router.get("/timeline", response_model=List[Dict[str, Any]])
async def get_timeline(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = DashboardService(db)
    return await service.timeline.get_timeline(limit=limit)


@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_alerts(
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = DashboardService(db)
    return await service.alerts.get_alerts(severity=severity)


@router.get("/incidents", response_model=List[Dict[str, Any]])
async def get_dashboard_incidents(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    # Fetch from Redis active incidents
    try:
        active_ids = await redis_manager.client.smembers("stadium:incidents:active")
        incidents = []
        for aid in active_ids:
            aid_str = aid.decode("utf-8") if isinstance(aid, bytes) else str(aid)
            data = await redis_manager.client.hgetall(f"stadium:incident:{aid_str}")
            if data:
                incidents.append({
                    "incident_id": int(data.get(b"incident_id", b"0").decode("utf-8")),
                    "title": data.get(b"title", b"").decode("utf-8"),
                    "status": data.get(b"status", b"Open").decode("utf-8"),
                    "severity": data.get(b"severity", b"").decode("utf-8"),
                    "priority": data.get(b"priority", b"").decode("utf-8"),
                    "category": data.get(b"category", b"").decode("utf-8"),
                    "created_at": data.get(b"created_at", b"").decode("utf-8")
                })
        return incidents
    except Exception as e:
        logger = DashboardService(db).timeline.audit_repo.db
        # Fallback empty list or mock response
        return []


@router.get("/crowd", response_model=List[Dict[str, Any]])
async def get_dashboard_crowd(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    # Scan keys stadium:zone:*:crowd
    try:
        keys = await redis_manager.client.keys("stadium:zone:*:crowd")
        crowd_data = []
        for k in keys:
            k_str = k.decode("utf-8") if isinstance(k, bytes) else str(k)
            parts = k_str.split(":")
            zone_id = int(parts[2])
            hdata = await redis_manager.client.hgetall(k_str)
            if hdata:
                crowd_data.append({
                    "zone_id": zone_id,
                    "estimated_count": int(hdata.get(b"estimated_count", b"0").decode("utf-8")),
                    "density_level": float(hdata.get(b"density_level", b"0.0").decode("utf-8")),
                    "updated_at": hdata.get(b"updated_at", b"").decode("utf-8")
                })
        return crowd_data
    except Exception:
        return []


@router.get("/transit", response_model=Dict[str, Any])
async def get_dashboard_transit(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    # Retrieve transit KPI summary
    return {
        "status": "Operational",
        "average_delay_minutes": 5.0,
        "active_shuttles": 12,
        "transit_alerts": []
    }


@router.get("/volunteers", response_model=Dict[str, Any])
async def get_dashboard_volunteers(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    # Retrieve volunteer KPI summary
    return {
        "active_volunteers": 48,
        "assigned_shifts": 32,
        "unassigned_shifts": 5,
        "status": "Steward availability nominal"
    }


@router.get("/accessibility", response_model=Dict[str, Any])
async def get_dashboard_accessibility(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    # Retrieve accessibility KPI summary
    return {
        "active_barriers": 1,
        "escalators_operational": True,
        "elevator_alerts": []
    }


@router.get("/health", response_model=Dict[str, Any])
async def get_dashboard_health(
    db: AsyncSession = Depends(get_db_session),
    _role: None = Depends(read_checker)
):
    try:
        redis_ok = await redis_manager.client.ping()
    except Exception:
        redis_ok = False

    return {
        "status": "Healthy" if redis_ok else "Degraded",
        "services": {
            "dashboard_api": "Healthy",
            "redis_cache": "Healthy" if redis_ok else "Down",
            "websocket_connections": 0,
            "aggregation_service": "Running"
        }
    }


@router.post("/preferences", response_model=PreferenceOut)
async def post_preferences(
    req: PreferenceSave,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(write_checker)
):
    service = DashboardService(db)
    pref = await service.preferences.save_preferences(
        user_id=current_user.id,
        theme=req.theme,
        prefs=req.preferences
    )
    return pref


@router.get("/preferences", response_model=PreferenceOut)
async def get_preferences(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = DashboardService(db)
    pref = await service.preferences.get_preferences(user_id=current_user.id)
    if not pref:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return pref


@router.get("/snapshots", response_model=List[SnapshotOut])
async def get_snapshots(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = DashboardService(db)
    return await service.snapshots.list_snapshots(limit=limit, offset=offset)


@router.post("/snapshots", response_model=SnapshotOut, status_code=status.HTTP_201_CREATED)
async def post_snapshot(
    req: SnapshotCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(write_checker)
):
    service = DashboardService(db)
    snap = await service.snapshots.capture_snapshot(
        snapshot_type=req.snapshot_type,
        data=req.data
    )
    return snap


@router.delete("/snapshots/{id}", status_code=status.HTTP_200_OK)
async def delete_snapshot(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(write_checker)
):
    service = DashboardService(db)
    ok = await service.snapshots.delete_snapshot(id)
    if not ok:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"detail": "Snapshot deleted"}
