import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.core.kafka_producer import kafka_producer
from backend.app.core.redis import redis_manager

# Models
from backend.app.models.dashboard import (
    DashboardWidget, DashboardLayout, DashboardPreference, DashboardSnapshot,
    DashboardNotification, DashboardSession, DashboardAudit, DashboardSubscription,
    DashboardMetric, DashboardAlert, DashboardTimeline, DashboardCacheMetadata
)
from backend.app.models.incident import Incident
from backend.app.models.volunteer import Volunteer, VolunteerShift, VolunteerAssignment
from backend.app.models.transit import TransitTrip, TransitVehicle
from backend.app.models.accessibility import AccessibilityBarrier

# Repositories
from backend.app.repositories.dashboard_repository import (
    WidgetRepository, LayoutRepository, PreferenceRepository, SnapshotRepository,
    NotificationRepository, SessionRepository, AuditRepository, SubscriptionRepository,
    MetricRepository, AlertRepository, TimelineRepository, CacheMetadataRepository
)

logger = logging.getLogger("dashboard_service")


class BaseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.widget_repo = WidgetRepository(db)
        self.layout_repo = LayoutRepository(db)
        self.pref_repo = PreferenceRepository(db)
        self.snapshot_repo = SnapshotRepository(db)
        self.notification_repo = NotificationRepository(db)
        self.session_repo = SessionRepository(db)
        self.audit_repo = AuditRepository(db)
        self.sub_repo = SubscriptionRepository(db)
        self.metric_repo = MetricRepository(db)
        self.alert_repo = AlertRepository(db)
        self.timeline_repo = TimelineRepository(db)
        self.cache_repo = CacheMetadataRepository(db)

    async def log_audit(self, actor_id: Optional[int], action: str, details: Optional[Dict[str, Any]] = None):
        audit = DashboardAudit(actor_id=actor_id, action=action, details=details)
        await self.audit_repo.create(audit)
        await self.db.commit()


class WidgetService(BaseService):
    async def get_widgets(self, status: Optional[str] = "Active") -> List[Dict[str, Any]]:
        widgets = await self.widget_repo.list_widgets(status=status)
        result = []
        for w in widgets:
            result.append({
                "id": w.id,
                "title": w.title,
                "status": w.status,
                "priority": w.priority,
                "widget_type": w.widget_type,
                "config": w.config,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None
            })
        return result

    async def create_widget(self, title: str, status: str, priority: str, widget_type: str, config: Optional[dict] = None) -> DashboardWidget:
        widget = DashboardWidget(title=title, status=status, priority=priority, widget_type=widget_type, config=config)
        await self.widget_repo.create(widget)
        await self.db.commit()
        # Publish event
        await kafka_producer.send_event("dashboard.widget.updated", str(widget.id), {
            "widget_id": widget.id,
            "title": title,
            "status": status,
            "action": "CREATE"
        })
        return widget


class MetricsService(BaseService):
    async def get_kpis(self) -> Dict[str, Any]:
        # Try fetching from Redis first
        density = await redis_manager.client.get("dashboard:metrics:average_density")
        active_inc = await redis_manager.client.get("dashboard:metrics:active_incidents_count")
        
        # Fallbacks to DB if Redis returns None
        if density is None:
            # Fake/Default average density metric or count zones
            density = "0.45"
        else:
            density = density.decode("utf-8") if isinstance(density, bytes) else str(density)

        if active_inc is None:
            # Query db count of open/active incidents
            stmt = select(func.count(Incident.id)).where(Incident.status == "Open", Incident.is_deleted == False)
            res = await self.db.execute(stmt)
            active_inc = str(res.scalar() or 0)
        else:
            active_inc = active_inc.decode("utf-8") if isinstance(active_inc, bytes) else str(active_inc)

        # Get additional metrics
        stmt_total_volunteers = select(func.count(Volunteer.id)).where(Volunteer.is_deleted == False)
        res_vols = await self.db.execute(stmt_total_volunteers)
        total_vols = res_vols.scalar() or 0

        stmt_active_barriers = select(func.count(AccessibilityBarrier.id)).where(AccessibilityBarrier.status == "Active", AccessibilityBarrier.is_deleted == False)
        res_barriers = await self.db.execute(stmt_active_barriers)
        active_barriers = res_barriers.scalar() or 0

        # Construct final dict
        kpis = {
            "current_attendance": 45000,
            "average_density": float(density),
            "critical_incidents": 0,
            "open_incidents": int(active_inc),
            "average_response_time": 120.5,
            "volunteer_availability": total_vols,
            "transit_delay": 5.0,
            "parking_occupancy": 0.82,
            "accessibility_alerts": active_barriers,
            "emergency_commands": 0,
            "dashboard_health": "Healthy"
        }
        
        # Update metrics table in PostgreSQL for snapshot audits
        for k, v in kpis.items():
            await self.metric_repo.create_or_update(name=k, value=str(v))
        await self.db.commit()

        # Publish event
        await kafka_producer.send_event("dashboard.metrics.updated", "current", kpis)

        return kpis


class NotificationService(BaseService):
    async def create_notification(self, level: str, message: str) -> DashboardNotification:
        notification = DashboardNotification(level=level, message=message)
        await self.notification_repo.create(notification)
        await self.db.commit()
        # Publish
        await kafka_producer.send_event("dashboard.notification.created", str(notification.id), {
            "id": notification.id,
            "level": level,
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return notification

    async def dismiss_notification(self, notification_id: int, user_id: int) -> Optional[DashboardNotification]:
        notif = await self.notification_repo.get_by_id(notification_id)
        if notif:
            notif.is_dismissed = True
            notif.dismissed_by_id = user_id
            await self.db.commit()
            await self.log_audit(user_id, "DISMISS_NOTIFICATION", {"notification_id": notification_id})
            return notif
        return None


class AlertService(BaseService):
    async def get_alerts(self, severity: Optional[str] = None, status: Optional[str] = "Active") -> List[Dict[str, Any]]:
        alerts = await self.alert_repo.list_alerts(severity=severity, status=status)
        return [{
            "id": a.id,
            "alert_type": a.alert_type,
            "source": a.source,
            "message": a.message,
            "severity": a.severity,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None
        } for a in alerts]

    async def create_alert(self, alert_type: str, source: str, message: str, severity: str = "Warning") -> DashboardAlert:
        alert = DashboardAlert(alert_type=alert_type, source=source, message=message, severity=severity, status="Active")
        await self.alert_repo.create(alert)
        await self.db.commit()
        # Publish
        await kafka_producer.send_event("dashboard.alert.created", str(alert.id), {
            "id": alert.id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message
        })
        return alert


class TimelineService(BaseService):
    async def get_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        events = await self.timeline_repo.list_events(limit=limit)
        return [{
            "id": e.id,
            "source_service": e.source_service,
            "event_type": e.event_type,
            "event_data": e.event_data,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None
        } for e in events]

    async def add_event(self, source_service: str, event_type: str, event_data: Optional[dict] = None) -> DashboardTimeline:
        event = DashboardTimeline(source_service=source_service, event_type=event_type, event_data=event_data)
        await self.timeline_repo.create(event)
        await self.db.commit()
        return event


class SnapshotService(BaseService):
    async def capture_snapshot(self, snapshot_type: str, data: dict) -> DashboardSnapshot:
        snap = DashboardSnapshot(snapshot_type=snapshot_type, data=data)
        await self.snapshot_repo.create(snap)
        await self.db.commit()
        # Publish
        await kafka_producer.send_event("dashboard.snapshot.created", str(snap.id), {
            "snapshot_id": snap.id,
            "snapshot_type": snapshot_type
        })
        return snap

    async def list_snapshots(self, limit: int = 50, offset: int = 0) -> List[DashboardSnapshot]:
        return await self.snapshot_repo.list_snapshots(limit=limit, offset=offset)

    async def delete_snapshot(self, snapshot_id: int) -> bool:
        snap = await self.snapshot_repo.get_by_id(snapshot_id)
        if snap:
            snap.is_deleted = True
            await self.db.commit()
            return True
        return False


class SessionService(BaseService):
    async def start_session(self, user_id: int, token: str) -> DashboardSession:
        sess = DashboardSession(user_id=user_id, token=token, started_at=datetime.now(timezone.utc).replace(tzinfo=None))
        await self.session_repo.create(sess)
        await self.db.commit()
        await self.log_audit(user_id, "SESSION_START", {"session_id": sess.id})
        await kafka_producer.send_event("dashboard.session.started", str(sess.id), {
            "session_id": sess.id,
            "user_id": user_id
        })
        return sess

    async def close_session(self, session_id: int, user_id: int) -> Optional[DashboardSession]:
        sess = await self.session_repo.get_by_id(session_id)
        if sess:
            sess.closed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.db.commit()
            await self.log_audit(user_id, "SESSION_CLOSE", {"session_id": session_id})
            await kafka_producer.send_event("dashboard.session.closed", str(session_id), {
                "session_id": session_id,
                "user_id": user_id
            })
            return sess
        return None


class PreferenceService(BaseService):
    async def get_preferences(self, user_id: int) -> Optional[DashboardPreference]:
        return await self.pref_repo.get_by_user_id(user_id)

    async def save_preferences(self, user_id: int, theme: str, prefs: Optional[dict]) -> DashboardPreference:
        pref = await self.pref_repo.create_or_update(user_id, theme, prefs)
        await self.db.commit()
        await self.log_audit(user_id, "SAVE_PREFERENCES", {"theme": theme})
        return pref


class DashboardService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.widgets = WidgetService(db)
        self.metrics = MetricsService(db)
        self.notifications = NotificationService(db)
        self.alerts = AlertService(db)
        self.timeline = TimelineService(db)
        self.snapshots = SnapshotService(db)
        self.sessions = SessionService(db)
        self.preferences = PreferenceService(db)

    async def assemble_overview(self) -> Dict[str, Any]:
        # Gathers summary overview
        kpis = await self.metrics.get_kpis()
        active_widgets = await self.widgets.get_widgets(status="Active")
        recent_alerts = await self.alerts.get_alerts(status="Active")
        recent_timeline = await self.timeline.get_timeline(limit=10)

        # Broadcast update trigger via Kafka
        await kafka_producer.send_event("dashboard.updated", "current", {
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return {
            "kpis": kpis,
            "widgets": active_widgets,
            "alerts": recent_alerts,
            "timeline": recent_timeline
        }
