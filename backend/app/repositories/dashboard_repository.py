from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import Optional, List, Tuple
from backend.app.models.dashboard import (
    DashboardWidget, DashboardLayout, DashboardPreference, DashboardSnapshot,
    DashboardNotification, DashboardSession, DashboardAudit, DashboardSubscription,
    DashboardMetric, DashboardAlert, DashboardTimeline, DashboardCacheMetadata
)

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def commit(self):
        await self.db.commit()

    async def flush(self):
        await self.db.flush()


class WidgetRepository(BaseRepository):
    async def get_by_id(self, widget_id: int) -> Optional[DashboardWidget]:
        stmt = select(DashboardWidget).where(
            DashboardWidget.id == widget_id,
            DashboardWidget.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_widgets(self, status: Optional[str] = None) -> List[DashboardWidget]:
        stmt = select(DashboardWidget).where(DashboardWidget.is_deleted == False)
        if status:
            stmt = stmt.where(DashboardWidget.status == status)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, widget: DashboardWidget) -> DashboardWidget:
        self.db.add(widget)
        return widget


class LayoutRepository(BaseRepository):
    async def get_by_id(self, layout_id: int) -> Optional[DashboardLayout]:
        stmt = select(DashboardLayout).where(
            DashboardLayout.id == layout_id,
            DashboardLayout.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> List[DashboardLayout]:
        stmt = select(DashboardLayout).where(
            DashboardLayout.user_id == user_id,
            DashboardLayout.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, layout: DashboardLayout) -> DashboardLayout:
        self.db.add(layout)
        return layout


class PreferenceRepository(BaseRepository):
    async def get_by_user_id(self, user_id: int) -> Optional[DashboardPreference]:
        stmt = select(DashboardPreference).where(
            DashboardPreference.user_id == user_id,
            DashboardPreference.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create_or_update(self, user_id: int, theme: str, prefs: Optional[dict]) -> DashboardPreference:
        existing = await self.get_by_user_id(user_id)
        if existing:
            existing.theme = theme
            existing.preferences = prefs
            return existing
        new_pref = DashboardPreference(user_id=user_id, theme=theme, preferences=prefs)
        self.db.add(new_pref)
        return new_pref


class SnapshotRepository(BaseRepository):
    async def get_by_id(self, snapshot_id: int) -> Optional[DashboardSnapshot]:
        stmt = select(DashboardSnapshot).where(
            DashboardSnapshot.id == snapshot_id,
            DashboardSnapshot.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_snapshots(self, limit: int = 50, offset: int = 0) -> List[DashboardSnapshot]:
        stmt = select(DashboardSnapshot).where(DashboardSnapshot.is_deleted == False).order_by(DashboardSnapshot.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, snapshot: DashboardSnapshot) -> DashboardSnapshot:
        self.db.add(snapshot)
        return snapshot


class NotificationRepository(BaseRepository):
    async def get_by_id(self, notification_id: int) -> Optional[DashboardNotification]:
        stmt = select(DashboardNotification).where(
            DashboardNotification.id == notification_id,
            DashboardNotification.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_notifications(self, level: Optional[str] = None, is_dismissed: Optional[bool] = None, limit: int = 50) -> List[DashboardNotification]:
        stmt = select(DashboardNotification).where(DashboardNotification.is_deleted == False)
        if level:
            stmt = stmt.where(DashboardNotification.level == level)
        if is_dismissed is not None:
            stmt = stmt.where(DashboardNotification.is_dismissed == is_dismissed)
        stmt = stmt.order_by(DashboardNotification.created_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, notification: DashboardNotification) -> DashboardNotification:
        self.db.add(notification)
        return notification


class SessionRepository(BaseRepository):
    async def get_by_id(self, session_id: int) -> Optional[DashboardSession]:
        stmt = select(DashboardSession).where(
            DashboardSession.id == session_id,
            DashboardSession.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_active_sessions(self) -> List[DashboardSession]:
        stmt = select(DashboardSession).where(
            DashboardSession.closed_at == None,
            DashboardSession.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, sess: DashboardSession) -> DashboardSession:
        self.db.add(sess)
        return sess


class AuditRepository(BaseRepository):
    async def list_audits(self, limit: int = 100) -> List[DashboardAudit]:
        stmt = select(DashboardAudit).where(DashboardAudit.is_deleted == False).order_by(DashboardAudit.created_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, audit: DashboardAudit) -> DashboardAudit:
        self.db.add(audit)
        return audit


class SubscriptionRepository(BaseRepository):
    async def list_subscriptions(self, channel: Optional[str] = None) -> List[DashboardSubscription]:
        stmt = select(DashboardSubscription).where(DashboardSubscription.is_deleted == False)
        if channel:
            stmt = stmt.where(DashboardSubscription.channel == channel)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, sub: DashboardSubscription) -> DashboardSubscription:
        self.db.add(sub)
        return sub

    async def delete_by_connection_id(self, connection_id: str):
        stmt = delete(DashboardSubscription).where(DashboardSubscription.connection_id == connection_id)
        await self.db.execute(stmt)


class MetricRepository(BaseRepository):
    async def get_by_name(self, name: str) -> Optional[DashboardMetric]:
        stmt = select(DashboardMetric).where(
            DashboardMetric.name == name,
            DashboardMetric.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create_or_update(self, name: str, value: str, dims: Optional[dict] = None) -> DashboardMetric:
        existing = await self.get_by_name(name)
        if existing:
            existing.value = value
            existing.dimensions = dims
            return existing
        metric = DashboardMetric(name=name, value=value, dimensions=dims)
        self.db.add(metric)
        return metric


class AlertRepository(BaseRepository):
    async def list_alerts(self, severity: Optional[str] = None, status: Optional[str] = None) -> List[DashboardAlert]:
        stmt = select(DashboardAlert).where(DashboardAlert.is_deleted == False)
        if severity:
            stmt = stmt.where(DashboardAlert.severity == severity)
        if status:
            stmt = stmt.where(DashboardAlert.status == status)
        stmt = stmt.order_by(DashboardAlert.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, alert: DashboardAlert) -> DashboardAlert:
        self.db.add(alert)
        return alert


class TimelineRepository(BaseRepository):
    async def list_events(self, limit: int = 50) -> List[DashboardTimeline]:
        stmt = select(DashboardTimeline).where(DashboardTimeline.is_deleted == False).order_by(DashboardTimeline.timestamp.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, event: DashboardTimeline) -> DashboardTimeline:
        self.db.add(event)
        return event


class CacheMetadataRepository(BaseRepository):
    async def get_by_key(self, key: str) -> Optional[DashboardCacheMetadata]:
        stmt = select(DashboardCacheMetadata).where(
            DashboardCacheMetadata.cache_key == key,
            DashboardCacheMetadata.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def set_metadata(self, key: str, ttl: int) -> DashboardCacheMetadata:
        from datetime import datetime, timezone
        existing = await self.get_by_key(key)
        if existing:
            existing.ttl_seconds = ttl
            existing.last_updated = datetime.now(timezone.utc).replace(tzinfo=None)
            return existing
        meta = DashboardCacheMetadata(cache_key=key, ttl_seconds=ttl, last_updated=datetime.now(timezone.utc).replace(tzinfo=None))
        self.db.add(meta)
        return meta
