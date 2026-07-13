from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.models.auth import Base

class CrowdZone(Base):
    __tablename__ = "crowd_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    cameras = relationship("Camera", back_populates="zone", cascade="all, delete-orphan")
    snapshots = relationship("CrowdSnapshot", back_populates="zone", cascade="all, delete-orphan")
    occupancy_history = relationship("OccupancyHistory", back_populates="zone", cascade="all, delete-orphan")
    alerts = relationship("CrowdAlert", back_populates="zone", cascade="all, delete-orphan")
    ingress_flows = relationship("IngressFlow", back_populates="zone", cascade="all, delete-orphan")
    egress_flows = relationship("EgressFlow", back_populates="zone", cascade="all, delete-orphan")
    thresholds = relationship("CrowdThreshold", back_populates="zone", cascade="all, delete-orphan")
    capacities = relationship("ZoneCapacity", back_populates="zone", cascade="all, delete-orphan")
    density_metrics = relationship("DensityMetrics", back_populates="zone", cascade="all, delete-orphan")
    heatmap_tiles = relationship("HeatmapTile", back_populates="zone", cascade="all, delete-orphan")


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    zone_id = Column(Integer, ForeignKey("crowd_zones.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, default="Active") # Active, Offline, Maintenance
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    zone = relationship("CrowdZone", back_populates="cameras")
    health_logs = relationship("CameraHealth", back_populates="camera", cascade="all, delete-orphan")
    snapshots = relationship("CrowdSnapshot", back_populates="camera")


class CameraHealth(Base):
    __tablename__ = "camera_health"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    connectivity_status = Column(String, nullable=False) # Connected, Disconnected
    latency_ms = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    recorded_at = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    camera = relationship("Camera", back_populates="health_logs")


class CrowdSnapshot(Base):
    __tablename__ = "crowd_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("crowd_zones.id", ondelete="CASCADE"), nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    estimated_count = Column(Integer, nullable=False)
    density_level = Column(Float, nullable=False)
    recorded_at = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    zone = relationship("CrowdZone", back_populates="snapshots")
    camera = relationship("Camera", back_populates="snapshots")


class OccupancyHistory(Base):
    __tablename__ = "occupancy_history"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("crowd_zones.id", ondelete="CASCADE"), nullable=False)
    occupancy_count = Column(Integer, nullable=False)
    capacity_utilization_ratio = Column(Float, nullable=False)
    timestamp = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    zone = relationship("CrowdZone", back_populates="occupancy_history")


class CrowdAlert(Base):
    __tablename__ = "crowd_alerts"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("crowd_zones.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String, nullable=False) # Overcrowding, Surge, CameraOffline
    severity = Column(String, nullable=False) # Info, Warning, Critical
    message = Column(String, nullable=False)
    triggered_at = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    resolved_at = Column(DateTime, nullable=True)

    zone = relationship("CrowdZone", back_populates="alerts")


class IngressFlow(Base):
    __tablename__ = "ingress_flows"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("crowd_zones.id", ondelete="CASCADE"), nullable=False)
    turnstile_id = Column(String, nullable=False)
    scan_rate_per_min = Column(Integer, nullable=False)
    timestamp = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    zone = relationship("CrowdZone", back_populates="ingress_flows")


class EgressFlow(Base):
    __tablename__ = "egress_flows"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("crowd_zones.id", ondelete="CASCADE"), nullable=False)
    exit_gate_id = Column(String, nullable=False)
    flow_velocity = Column(Float, nullable=False)
    dispersal_rate_per_min = Column(Integer, nullable=False)
    timestamp = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    zone = relationship("CrowdZone", back_populates="egress_flows")


class DensityMetrics(Base):
    __tablename__ = "density_metrics"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("crowd_zones.id", ondelete="CASCADE"), nullable=False)
    average_density = Column(Float, nullable=False)
    peak_density = Column(Float, nullable=False)
    timestamp = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    zone = relationship("CrowdZone", back_populates="density_metrics")


class HeatmapTile(Base):
    __tablename__ = "heatmap_tiles"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("crowd_zones.id", ondelete="CASCADE"), nullable=False)
    x_coord = Column(Integer, nullable=False)
    y_coord = Column(Integer, nullable=False)
    density_val = Column(Float, nullable=False)
    timestamp = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    zone = relationship("CrowdZone", back_populates="heatmap_tiles")


class CrowdThreshold(Base):
    __tablename__ = "crowd_thresholds"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("crowd_zones.id", ondelete="CASCADE"), nullable=False)
    threshold_type = Column(String, nullable=False) # OccupancyWarning, OccupancyCritical, DensityCritical
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    zone = relationship("CrowdZone", back_populates="thresholds")


class ZoneCapacity(Base):
    __tablename__ = "zone_capacities"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("crowd_zones.id", ondelete="CASCADE"), nullable=False)
    max_capacity = Column(Integer, nullable=False)
    safe_capacity_limit = Column(Integer, nullable=False)

    zone = relationship("CrowdZone", back_populates="capacities")
