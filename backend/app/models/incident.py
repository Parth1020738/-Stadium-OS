from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.models.auth import Base

# Many-to-many relationship mapping incident assignment to stewards/responders (users)
incident_assignments_association = Table(
    "incident_assignments_association",
    Base.metadata,
    Column("incident_id", Integer, ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Severity: Low, Medium, High, Critical
    severity = Column(String(50), nullable=False, default="Medium")
    # Priority: Low, Medium, High, Critical
    priority = Column(String(50), nullable=False, default="Medium")
    # Category: Medical, Security, CrowdControl, Facility, Transit, Weather, Fire, Other
    category = Column(String(50), nullable=False, default="Security")
    # Status: Open, Assigned, Escalated, Resolved, Closed
    status = Column(String(50), nullable=False, default="Open")
    
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    location_zone = Column(String(255), nullable=True)
    location_details = Column(String(255), nullable=True)
    
    sla_minutes = Column(Integer, nullable=False, default=15)
    sla_expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    closed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id])
    assigned_responders = relationship("User", secondary=incident_assignments_association)
    
    timeline_entries = relationship("IncidentTimeline", back_populates="incident", cascade="all, delete-orphan")
    evidence_entries = relationship("IncidentEvidence", back_populates="incident", cascade="all, delete-orphan")
    attachments = relationship("IncidentAttachment", back_populates="incident", cascade="all, delete-orphan")
    comments = relationship("IncidentComment", back_populates="incident", cascade="all, delete-orphan")
    assignments = relationship("IncidentAssignment", back_populates="incident", cascade="all, delete-orphan")
    resolutions = relationship("IncidentResolution", back_populates="incident", cascade="all, delete-orphan")
    escalations = relationship("IncidentEscalation", back_populates="incident", cascade="all, delete-orphan")
    notifications = relationship("IncidentNotification", back_populates="incident", cascade="all, delete-orphan")
    audits = relationship("IncidentAudit", back_populates="incident", cascade="all, delete-orphan")


class IncidentTimeline(Base):
    __tablename__ = "incident_timeline"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False) # e.g. Created, Assigned, Escalated, Resolved, CommentAdded
    description = Column(Text, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    incident = relationship("Incident", back_populates="timeline_entries")
    created_by = relationship("User")


class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    evidence_type = Column(String(100), nullable=False) # e.g., Photo, Video, Audio, Log
    description = Column(Text, nullable=True)
    storage_uri = Column(String(1024), nullable=False)
    checksum_sha256 = Column(String(64), nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    incident = relationship("Incident", back_populates="evidence_entries")
    uploaded_by = relationship("User")


class IncidentAttachment(Base):
    __tablename__ = "incident_attachments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_provider = Column(String(50), nullable=False, default="local")
    storage_uri = Column(String(1024), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    incident = relationship("Incident", back_populates="attachments")
    uploaded_by = relationship("User")


class IncidentComment(Base):
    __tablename__ = "incident_comments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    comment_text = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    incident = relationship("Incident", back_populates="comments")
    author = relationship("User")


class IncidentAssignment(Base):
    __tablename__ = "incident_assignments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    status = Column(String(50), nullable=False, default="Assigned") # Assigned, Accepted, Rejected, Completed

    incident = relationship("Incident", back_populates="assignments")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])


class IncidentResolution(Base):
    __tablename__ = "incident_resolutions"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    resolution_summary = Column(Text, nullable=False)
    resolved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    root_cause = Column(String(255), nullable=True)

    incident = relationship("Incident", back_populates="resolutions")
    resolved_by = relationship("User")


class IncidentEscalation(Base):
    __tablename__ = "incident_escalations"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    escalated_from_status = Column(String(50), nullable=False)
    escalated_to_status = Column(String(50), nullable=False)
    escalation_reason = Column(Text, nullable=False)
    escalated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    escalated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    incident = relationship("Incident", back_populates="escalations")
    escalated_by = relationship("User")


class IncidentNotification(Base):
    __tablename__ = "incident_notifications"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type = Column(String(50), nullable=False) # e.g. Push, SMS, Email, PAVA
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    status = Column(String(50), nullable=False, default="Sent")

    incident = relationship("Incident", back_populates="notifications")
    recipient = relationship("User")


class IncidentAudit(Base):
    __tablename__ = "incident_audits"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False) # e.g. CREATE, UPDATE, CLOSE, ASSIGN
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    changes_json = Column(Text, nullable=True) # JSON string of changed values

    incident = relationship("Incident", back_populates="audits")
    actor = relationship("User")
