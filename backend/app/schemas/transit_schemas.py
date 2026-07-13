from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any

# --- Shared Base Responses ---
class TransitStopResponse(BaseModel):
    id: int
    name: str
    stop_code: str
    latitude: float
    longitude: float
    version_id: int

    class Config:
        from_attributes = True


class TransitRouteResponse(BaseModel):
    id: int
    name: str
    route_code: str
    route_type: str
    status: str
    description: Optional[str] = None
    version_id: int

    class Config:
        from_attributes = True


class TransitVehicleResponse(BaseModel):
    id: int
    vehicle_code: str
    license_plate: str
    vehicle_type: str
    capacity: int
    status: str
    version_id: int

    class Config:
        from_attributes = True


class DriverResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    license_number: str
    phone: Optional[str] = None
    status: str
    version_id: int

    class Config:
        from_attributes = True


class OperatorResponse(BaseModel):
    id: int
    name: str
    contact_email: str
    phone: Optional[str] = None
    version_id: int

    class Config:
        from_attributes = True


class TransitHubResponse(BaseModel):
    id: int
    name: str
    location_zone: str
    capacity_status: str
    version_id: int

    class Config:
        from_attributes = True


class ParkingZoneResponse(BaseModel):
    id: int
    name: str
    total_spaces: int
    occupied_spaces: int
    location_zone: str
    status: str
    version_id: int

    class Config:
        from_attributes = True


class ShuttleServiceResponse(BaseModel):
    id: int
    name: str
    route_id: int
    frequency_minutes: int
    operating_hours: Optional[str] = None
    version_id: int

    class Config:
        from_attributes = True


class VehicleAssignmentResponse(BaseModel):
    id: int
    vehicle_id: int
    route_id: int
    status: str
    version_id: int

    class Config:
        from_attributes = True


class DriverAssignmentResponse(BaseModel):
    id: int
    driver_id: int
    vehicle_id: int
    assigned_at: datetime
    status: str
    version_id: int

    class Config:
        from_attributes = True


class TransitScheduleResponse(BaseModel):
    id: int
    route_id: int
    day_of_week: int
    departure_time: str
    arrival_time: str
    version_id: int

    class Config:
        from_attributes = True


class TransitTripResponse(BaseModel):
    id: int
    schedule_id: int
    vehicle_id: int
    driver_id: int
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: str
    version_id: int

    class Config:
        from_attributes = True


class TransitTelemetryResponse(BaseModel):
    id: int
    vehicle_id: int
    latitude: float
    longitude: float
    speed: float
    heading: float
    timestamp: datetime

    class Config:
        from_attributes = True


class TransitDelayResponse(BaseModel):
    id: int
    trip_id: int
    delay_minutes: int
    reason: Optional[str] = None
    reported_at: datetime
    version_id: int

    class Config:
        from_attributes = True


class TransitCapacityResponse(BaseModel):
    id: int
    vehicle_id: int
    max_seats: int
    max_standing: int
    version_id: int

    class Config:
        from_attributes = True


class TransitOccupancyResponse(BaseModel):
    id: int
    vehicle_id: int
    stop_id: int
    passenger_count: int
    timestamp: datetime
    version_id: int

    class Config:
        from_attributes = True


class TransitQueueResponse(BaseModel):
    id: int
    stop_id: int
    queue_size: int
    average_wait_time_minutes: float
    timestamp: datetime
    version_id: int

    class Config:
        from_attributes = True


class TransitETAResponse(BaseModel):
    id: int
    trip_id: int
    stop_id: int
    estimated_arrival: datetime
    version_id: int

    class Config:
        from_attributes = True


class TransitIncidentLinkResponse(BaseModel):
    id: int
    incident_id: int
    route_id: Optional[int] = None
    trip_id: Optional[int] = None
    status: str
    version_id: int

    class Config:
        from_attributes = True


class TransitAuditResponse(BaseModel):
    id: int
    action: str
    actor_id: Optional[int] = None
    target_type: str
    target_id: Optional[int] = None
    changes: Optional[str] = None
    timestamp: datetime
    version_id: int

    class Config:
        from_attributes = True


# --- Pagination and Statistics ---
class TransitPaginationResponse(BaseModel):
    total: int
    limit: int
    offset: int
    results: List[TransitRouteResponse]

    class Config:
        from_attributes = True


class TransitStatisticsResponse(BaseModel):
    total_routes: int
    delayed_routes: int
    suspended_routes: int
    total_vehicles: int
    active_vehicles: int
    maintenance_vehicles: int
    total_trips: int
    completed_trips: int
    average_delay_minutes: float


# --- REST API Envelope DTOs ---

# 1. Alert Ingestion Schema
class TransitAlertData(BaseModel):
    route_id: str
    hub_id: str
    alert_type: str
    severity: str
    delay_minutes: int
    reason: str
    estimated_resolution_time: Optional[datetime] = None


class TransitAlertRequest(BaseModel):
    traceId: str
    correlationId: str
    clientTimestamp: datetime
    clientVersion: str
    data: TransitAlertData


class TransitAlertResponseData(BaseModel):
    alert_id: str
    status: str
    downstream_triggers_triggered: bool


class TransitAlertResponseEnvelope(BaseModel):
    traceId: str
    correlationId: str
    serverTimestamp: datetime
    executionDurationMs: int
    metadata: dict = Field(default_factory=dict)
    data: TransitAlertResponseData
    error: Optional[Any] = None


# 2. Egress Pacing Schema
class TransitEgressPacingData(BaseModel):
    venue_id: str
    gate_ids: List[str]
    pacing_rate_limit_per_minute: int
    calculation_model: str
    authorized_user_id: str


class TransitEgressPacingRequest(BaseModel):
    traceId: str
    correlationId: str
    clientTimestamp: datetime
    clientVersion: str
    data: TransitEgressPacingData


class GatePacingStatus(BaseModel):
    gate_id: str
    pacing_status: str
    pacing_rate_limit_per_minute: int


class TransitEgressPacingResponseData(BaseModel):
    pacing_transaction_id: str
    gates_configured: List[GatePacingStatus]
    estimated_platform_clearance_delay_seconds: int


class TransitEgressPacingResponseEnvelope(BaseModel):
    traceId: str
    correlationId: str
    serverTimestamp: datetime
    executionDurationMs: int
    metadata: dict = Field(default_factory=dict)
    data: TransitEgressPacingResponseData
    error: Optional[Any] = None


# --- CRUD Requests ---
class CreateRouteRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    route_code: str = Field(..., min_length=1, max_length=50)
    route_type: str = Field("Bus", pattern="^(Bus|Metro|LightRail|Shuttle)$")
    description: Optional[str] = None


class CreateVehicleRequest(BaseModel):
    vehicle_code: str = Field(..., min_length=1, max_length=50)
    license_plate: str = Field(..., min_length=1, max_length=50)
    vehicle_type: str = Field("Bus", pattern="^(Bus|Train|Shuttle)$")
    capacity: int = Field(..., ge=1)


class AssignVehicleRequest(BaseModel):
    vehicle_id: int
    route_id: int


class AssignDriverRequest(BaseModel):
    driver_id: int
    vehicle_id: int


class CreateScheduleRequest(BaseModel):
    route_id: int
    day_of_week: int = Field(..., ge=0, le=6)
    departure_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    arrival_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")


class RecordTelemetryRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed: float = Field(..., ge=0.0)
    heading: float = Field(0.0, ge=0.0, le=360.0)
