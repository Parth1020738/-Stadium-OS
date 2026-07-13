from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.models.auth import Base

class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="Active") # Active, Inactive
    priority = Column(String(50), nullable=False, default="Medium") # Low, Medium, High, Critical
    widget_type = Column(String(100), nullable=False)
    config = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class DashboardLayout(Base):
    __tablename__ = "dashboard_layouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, default="Default")
    layout_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    user = relationship("User")


class DashboardPreference(Base):
    __tablename__ = "dashboard_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    theme = Column(String(50), nullable=False, default="dark")
    preferences = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    user = relationship("User")


class DashboardSnapshot(Base):
    __tablename__ = "dashboard_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_type = Column(String(100), nullable=False)
    data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class DashboardNotification(Base):
    __tablename__ = "dashboard_notifications"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(50), nullable=False, default="Info") # Info, Warning, Critical, Emergency
    message = Column(Text, nullable=False)
    is_dismissed = Column(Boolean, default=False, nullable=False)
    dismissed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    dismissed_by = relationship("User", foreign_keys=[dismissed_by_id])


class DashboardSession(Base):
    __tablename__ = "dashboard_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    closed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    user = relationship("User")


class DashboardAudit(Base):
    __tablename__ = "dashboard_audits"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    actor = relationship("User")


class DashboardSubscription(Base):
    __tablename__ = "dashboard_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(String(255), nullable=False)
    channel = Column(String(100), nullable=False)
    filters = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class DashboardMetric(Base):
    __tablename__ = "dashboard_metrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    value = Column(String(255), nullable=False)
    dimensions = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class DashboardAlert(Base):
    __tablename__ = "dashboard_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100), nullable=False)
    source = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, default="Warning") # Info, Warning, Critical, Emergency
    status = Column(String(50), nullable=False, default="Active") # Active, Resolved, Dismissed

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class DashboardTimeline(Base):
    __tablename__ = "dashboard_timeline"

    id = Column(Integer, primary_key=True, index=True)
    source_service = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class DashboardCacheMetadata(Base):
    __tablename__ = "dashboard_cache_metadata"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), nullable=False, unique=True)
    ttl_seconds = Column(Integer, nullable=False, default=300)
    last_updated = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }
