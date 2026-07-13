from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Optional, List, Any

# UTC Datetime helper validator
def ensure_utc(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, str):
        try:
            # Try parsing with ISO-8601 formatting, adjusting for 'Z'
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Invalid datetime format. Expected ISO-8601.")
    if isinstance(v, datetime):
        if v.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware (contain timezone offset or 'Z').")
        return v.astimezone(timezone.utc)
    raise ValueError("Invalid datetime type.")


# Waypoint Schemas
class WaypointResponse(BaseModel):
    id: str
    route_id: str
    step_index: int
    direction: str
    instruction: str
    audio_uri: Optional[str] = None

    class Config:
        from_attributes = True


# Route Schemas
class RouteCreateRequest(BaseModel):
    start_zone_id: str
    end_zone_id: str
    impairment_profile: str
    generate_audio_instructions: Optional[bool] = False
    audio_language: Optional[str] = "en"

class RouteResponse(BaseModel):
    id: str
    venue_id: str
    start_zone_id: str
    end_zone_id: str
    impairment_profile: str
    route_length_meters: float
    estimated_travel_time_seconds: int
    status: str
    waypoints: List[WaypointResponse] = []

    class Config:
        from_attributes = True


# Barrier Schemas
class BarrierCreateData(BaseModel):
    barrier_type: str
    severity: str
    zone_id: str
    location_label: str
    associated_facility_id: Optional[str] = None
    latitude: float
    longitude: float
    bms_fault_code: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator("expires_at", mode="before")
    @classmethod
    def validate_expires_at(cls, v: Any) -> Any:
        return ensure_utc(v)

class BarrierCreateRequest(BaseModel):
    traceId: str
    correlationId: str
    clientTimestamp: datetime
    clientVersion: str
    data: BarrierCreateData

    @field_validator("clientTimestamp", mode="before")
    @classmethod
    def validate_client_timestamp(cls, v: Any) -> Any:
        return ensure_utc(v)

class BarrierCreateResponseData(BaseModel):
    barrier_id: str
    status: str
    impacted_routes_count: int
    reroute_command_triggered: bool

class BarrierCreateResponseEnvelope(BaseModel):
    traceId: str
    correlationId: str
    serverTimestamp: datetime
    executionDurationMs: int
    metadata: dict = {}
    data: BarrierCreateResponseData
    error: Optional[Any] = None

    @field_validator("serverTimestamp", mode="before")
    @classmethod
    def validate_server_timestamp(cls, v: Any) -> Any:
        return ensure_utc(v)

class BarrierUpdateRequest(BaseModel):
    barrier_type: Optional[str] = None
    severity: Optional[str] = None
    zone_id: Optional[str] = None
    location_label: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator("expires_at", mode="before")
    @classmethod
    def validate_expires_at(cls, v: Any) -> Any:
        return ensure_utc(v)

class BarrierResponse(BaseModel):
    id: str
    venue_id: str
    barrier_type: str
    severity: str
    zone_id: str
    location_label: str
    associated_facility_id: Optional[str] = None
    latitude: float
    longitude: float
    bms_fault_code: Optional[str] = None
    status: str
    expires_at: Optional[datetime] = None
    version_id: int

    @field_validator("expires_at", mode="before")
    @classmethod
    def validate_expires_at(cls, v: Any) -> Any:
        return ensure_utc(v)

    class Config:
        from_attributes = True


# Route Generation Envelope
class RouteCreateResponseEnvelope(BaseModel):
    traceId: str
    correlationId: str
    serverTimestamp: datetime
    executionDurationMs: int
    metadata: dict = {}
    data: RouteResponse
    error: Optional[Any] = None

    @field_validator("serverTimestamp", mode="before")
    @classmethod
    def validate_server_timestamp(cls, v: Any) -> Any:
        return ensure_utc(v)


# Facility Schemas
class ElevatorStatusResponse(BaseModel):
    is_operational: bool
    bms_fault_code: Optional[str] = None
    last_telemetry_time: datetime

    @field_validator("last_telemetry_time", mode="before")
    @classmethod
    def validate_telemetry_time(cls, v: Any) -> Any:
        return ensure_utc(v)

    class Config:
        from_attributes = True

class RampStatusResponse(BaseModel):
    is_obstructed: bool
    obstruction_description: Optional[str] = None

    class Config:
        from_attributes = True

class AccessibleEntranceResponse(BaseModel):
    queue_length_seconds: int
    is_open: bool

    class Config:
        from_attributes = True

class FacilityResponse(BaseModel):
    id: str
    venue_id: str
    name: str
    facility_type: str
    status: str
    elevator_status: Optional[ElevatorStatusResponse] = None
    ramp_status: Optional[RampStatusResponse] = None
    entrance_status: Optional[AccessibleEntranceResponse] = None
    version_id: int

    class Config:
        from_attributes = True


# Map Schemas
class MapResponse(BaseModel):
    id: str
    venue_id: str
    map_data: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


# Alert Schemas
class AlertResponse(BaseModel):
    id: str
    venue_id: str
    title: str
    message: str
    severity: str
    status: str
    barrier_id: Optional[str] = None

    class Config:
        from_attributes = True
