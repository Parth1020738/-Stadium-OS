from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, List

class UserMinimalOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True

# ----------------- Requests -----------------

class CreateIncidentRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    severity: str = Field("Medium", pattern="^(Low|Medium|High|Critical)$")
    priority: str = Field("Medium", pattern="^(Low|Medium|High|Critical)$")
    category: str = Field("Security", pattern="^(Medical|Security|CrowdControl|Facility|Transit|Weather|Fire|Other)$")
    location_zone: Optional[str] = Field(None, max_length=255)
    location_details: Optional[str] = Field(None, max_length=255)
    sla_minutes: Optional[int] = Field(15, gt=0)


class UpdateIncidentRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    severity: Optional[str] = Field(None, pattern="^(Low|Medium|High|Critical)$")
    priority: Optional[str] = Field(None, pattern="^(Low|Medium|High|Critical)$")
    category: Optional[str] = Field(None, pattern="^(Medical|Security|CrowdControl|Facility|Transit|Weather|Fire|Other)$")
    location_zone: Optional[str] = Field(None, max_length=255)
    location_details: Optional[str] = Field(None, max_length=255)
    version_id: int


class AssignIncidentRequest(BaseModel):
    assigned_user_id: int


class ResolveIncidentRequest(BaseModel):
    resolution_summary: str = Field(..., min_length=10)
    root_cause: Optional[str] = Field(None, max_length=255)


class EscalationRequest(BaseModel):
    escalation_reason: str = Field(..., min_length=5)
    escalated_to_status: str = Field("Escalated", pattern="^(Escalated)$")


class CommentRequest(BaseModel):
    comment_text: str = Field(..., min_length=1)


class EvidenceRequest(BaseModel):
    evidence_type: str = Field(..., pattern="^(Photo|Video|Audio|Log)$")
    description: Optional[str] = None
    storage_uri: str = Field(..., min_length=5)
    checksum_sha256: Optional[str] = Field(None, min_length=64, max_length=64)


class AttachmentRequest(BaseModel):
    filename: str = Field(..., min_length=1)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., min_length=3)
    storage_uri: str = Field(..., min_length=5)

# ----------------- Responses -----------------

class TimelineResponse(BaseModel):
    id: int
    incident_id: int
    event_type: str
    description: str
    created_by: Optional[UserMinimalOut] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceResponse(BaseModel):
    id: int
    incident_id: int
    evidence_type: str
    description: Optional[str] = None
    storage_uri: str
    checksum_sha256: Optional[str] = None
    uploaded_by: Optional[UserMinimalOut] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class AttachmentResponse(BaseModel):
    id: int
    incident_id: int
    filename: str
    file_size: int
    mime_type: str
    storage_provider: str
    storage_uri: str
    uploaded_by: Optional[UserMinimalOut] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    id: int
    incident_id: int
    comment_text: str
    author: Optional[UserMinimalOut] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignmentResponse(BaseModel):
    id: int
    incident_id: int
    assigned_user: UserMinimalOut
    assigned_by: Optional[UserMinimalOut] = None
    assigned_at: datetime
    status: str

    class Config:
        from_attributes = True


class ResolutionResponse(BaseModel):
    id: int
    incident_id: int
    resolution_summary: str
    resolved_by: Optional[UserMinimalOut] = None
    resolved_at: datetime
    root_cause: Optional[str] = None

    class Config:
        from_attributes = True


class EscalationResponse(BaseModel):
    id: int
    incident_id: int
    escalated_from_status: str
    escalated_to_status: str
    escalation_reason: str
    escalated_by: Optional[UserMinimalOut] = None
    escalated_at: datetime

    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    priority: str
    category: str
    status: str
    reporter: Optional[UserMinimalOut] = None
    location_zone: Optional[str] = None
    location_details: Optional[str] = None
    sla_minutes: int
    sla_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    version_id: int
    assigned_responders: List[UserMinimalOut] = []

    class Config:
        from_attributes = True


class StatisticsResponse(BaseModel):
    total_incidents: int
    open_incidents: int
    assigned_incidents: int
    resolved_incidents: int
    closed_incidents: int
    critical_priority_count: int


class PaginationResponse(BaseModel):
    items: List[IncidentResponse]
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    detail: str
