import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship as orm_relationship
from backend.app.models.auth import Base

class AccessibilityBarrier(Base):
    __tablename__ = "accessibility_barriers"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    venue_id = Column(String(50), nullable=False, index=True)
    barrier_type = Column(String(100), nullable=False, index=True)  # ELEVATOR_OUTAGE, RAMP_CLOSED, etc.
    severity = Column(String(50), nullable=False, index=True)  # CRITICAL, MAJOR, MINOR
    zone_id = Column(String(100), nullable=False, index=True)
    location_label = Column(String(255), nullable=False)
    associated_facility_id = Column(String(36), ForeignKey("accessibility_facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    bms_fault_code = Column(String(100), nullable=True)
    status = Column(String(50), default="Active", nullable=False, index=True)  # Active, Resolved, Expired
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    facility = orm_relationship("AccessibilityFacility", back_populates="barriers")
    alerts = orm_relationship("AccessibilityAlert", back_populates="barrier")


class AccessibilityRoute(Base):
    __tablename__ = "accessibility_routes"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    venue_id = Column(String(50), nullable=False, index=True)
    start_zone_id = Column(String(100), nullable=False)
    end_zone_id = Column(String(100), nullable=False)
    impairment_profile = Column(String(100), nullable=False)  # WHEELCHAIR_ACCESSIBLE, etc.
    route_length_meters = Column(Float, nullable=False)
    estimated_travel_time_seconds = Column(Integer, nullable=False)
    status = Column(String(50), default="Active", nullable=False, index=True)  # Active, ObstructionDetected, Recalculated

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    waypoints = orm_relationship("AccessibilityWaypoint", back_populates="route", cascade="all, delete-orphan")


class AccessibilityWaypoint(Base):
    __tablename__ = "accessibility_waypoints"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    route_id = Column(String(36), ForeignKey("accessibility_routes.id", ondelete="CASCADE"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    direction = Column(String(50), nullable=False)
    instruction = Column(Text, nullable=False)
    audio_uri = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    route = orm_relationship("AccessibilityRoute", back_populates="waypoints")


class AccessibilityFacility(Base):
    __tablename__ = "accessibility_facilities"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    venue_id = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    facility_type = Column(String(50), nullable=False, index=True)  # ELEVATOR, RAMP, ENTRANCE, RESTROOM
    status = Column(String(50), default="Active", nullable=False, index=True)  # Active, Inactive

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    barriers = orm_relationship("AccessibilityBarrier", back_populates="facility")
    elevator_status = orm_relationship("ElevatorStatus", back_populates="facility", uselist=False, cascade="all, delete-orphan")
    ramp_status = orm_relationship("RampStatus", back_populates="facility", uselist=False, cascade="all, delete-orphan")
    entrance_status = orm_relationship("AccessibleEntrance", back_populates="facility", uselist=False, cascade="all, delete-orphan")


class AccessibilityMap(Base):
    __tablename__ = "accessibility_maps"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    venue_id = Column(String(50), nullable=False, unique=True, index=True)
    map_data = Column(Text, nullable=True)
    status = Column(String(50), default="Active", nullable=False, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class ElevatorStatus(Base):
    __tablename__ = "elevator_statuses"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("accessibility_facilities.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    is_operational = Column(Boolean, default=True, nullable=False, index=True)
    bms_fault_code = Column(String(100), nullable=True)
    last_telemetry_time = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    facility = orm_relationship("AccessibilityFacility", back_populates="elevator_status")


class RampStatus(Base):
    __tablename__ = "ramp_statuses"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("accessibility_facilities.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    is_obstructed = Column(Boolean, default=False, nullable=False, index=True)
    obstruction_description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    facility = orm_relationship("AccessibilityFacility", back_populates="ramp_status")


class AccessibleEntrance(Base):
    __tablename__ = "accessible_entrances"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("accessibility_facilities.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    queue_length_seconds = Column(Integer, default=0, nullable=False)
    is_open = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    facility = orm_relationship("AccessibilityFacility", back_populates="entrance_status")


class AccessibilityAlert(Base):
    __tablename__ = "accessibility_alerts"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    venue_id = Column(String(50), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, index=True)  # CRITICAL, WARNING, INFO
    status = Column(String(50), default="Active", nullable=False, index=True)  # Active, Resolved
    barrier_id = Column(String(36), ForeignKey("accessibility_barriers.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    barrier = orm_relationship("AccessibilityBarrier", back_populates="alerts")


class AccessibilityAudit(Base):
    __tablename__ = "accessibility_audits"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    venue_id = Column(String(50), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }
