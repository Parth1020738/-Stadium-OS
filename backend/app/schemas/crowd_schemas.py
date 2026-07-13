from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List

# --- Category & Tag DTOs ---

class ZoneCapacityCreate(BaseModel):
    max_capacity: int = Field(..., gt=0)
    safe_capacity_limit: int = Field(..., gt=0)

    @field_validator("safe_capacity_limit")
    @classmethod
    def validate_limits(cls, safe_limit: int, info) -> int:
        max_cap = info.data.get("max_capacity")
        if max_cap and safe_limit > max_cap:
            raise ValueError("Safe capacity limit cannot exceed max capacity")
        return safe_limit

class ZoneCapacityOut(BaseModel):
    id: int
    zone_id: int
    max_capacity: int
    safe_capacity_limit: int

    class Config:
        from_attributes = True


class CrowdThresholdCreate(BaseModel):
    threshold_type: str = Field(..., pattern="^(OccupancyWarning|OccupancyCritical|DensityCritical)$")
    value: float = Field(..., ge=0.0)

class CrowdThresholdOut(BaseModel):
    id: int
    zone_id: int
    threshold_type: str
    value: float

    class Config:
        from_attributes = True


# --- Camera DTOs ---

class CameraCreate(BaseModel):
    device_id: str = Field(..., min_length=2)
    name: str = Field(..., min_length=2)
    zone_id: Optional[int] = None
    status: Optional[str] = "Active"
    ip_address: Optional[str] = None

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    zone_id: Optional[int] = None
    status: Optional[str] = None
    ip_address: Optional[str] = None

class CameraOut(BaseModel):
    id: int
    device_id: str
    name: str
    zone_id: Optional[int]
    status: str
    ip_address: Optional[str]
    created_at: datetime
    updated_at: datetime
    version_id: int

    class Config:
        from_attributes = True


class CameraHealthCreate(BaseModel):
    connectivity_status: str = Field(..., pattern="^(Connected|Disconnected)$")
    latency_ms: Optional[int] = Field(None, ge=0)
    fps: Optional[float] = Field(None, ge=0.0)

class CameraHealthOut(BaseModel):
    id: int
    camera_id: int
    connectivity_status: str
    latency_ms: Optional[int]
    fps: Optional[float]
    recorded_at: datetime

    class Config:
        from_attributes = True


# --- Zone DTOs ---

class CrowdZoneCreate(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = None

class CrowdZoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CrowdZoneOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    version_id: int
    cameras: List[CameraOut] = []
    thresholds: List[CrowdThresholdOut] = []
    capacities: List[ZoneCapacityOut] = []

    class Config:
        from_attributes = True


# --- Snapshot DTOs ---

class CrowdSnapshotCreate(BaseModel):
    zone_id: int
    camera_id: Optional[int] = None
    estimated_count: int = Field(..., ge=0)
    density_level: float = Field(..., ge=0.0)
    recorded_at: Optional[datetime] = None

class CrowdSnapshotUpdate(BaseModel):
    estimated_count: int = Field(..., ge=0)
    density_level: float = Field(..., ge=0.0)

class CrowdSnapshotOut(BaseModel):
    id: int
    zone_id: int
    camera_id: Optional[int]
    estimated_count: int
    density_level: float
    recorded_at: datetime

    class Config:
        from_attributes = True


# --- Occupancy DTOs ---

class OccupancyCreate(BaseModel):
    occupancy_count: int = Field(..., ge=0)

class OccupancyHistoryOut(BaseModel):
    id: int
    zone_id: int
    occupancy_count: int
    capacity_utilization_ratio: float
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Density DTOs ---

class DensityMetricsCreate(BaseModel):
    average_density: float = Field(..., ge=0.0)
    peak_density: float = Field(..., ge=0.0)

class DensityMetricsOut(BaseModel):
    id: int
    zone_id: int
    average_density: float
    peak_density: float
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Flow DTOs ---

class IngressFlowCreate(BaseModel):
    turnstile_id: str
    scan_rate_per_min: int = Field(..., ge=0)

class IngressFlowOut(BaseModel):
    id: int
    zone_id: int
    turnstile_id: str
    scan_rate_per_min: int
    timestamp: datetime

    class Config:
        from_attributes = True


class EgressFlowCreate(BaseModel):
    exit_gate_id: str
    flow_velocity: float = Field(..., ge=0.0)
    dispersal_rate_per_min: int = Field(..., ge=0)

class EgressFlowOut(BaseModel):
    id: int
    zone_id: int
    exit_gate_id: str
    flow_velocity: float
    dispersal_rate_per_min: int
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Heatmap DTOs ---

class HeatmapTileCreate(BaseModel):
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    val: float = Field(..., ge=0.0)

class HeatmapTileOut(BaseModel):
    id: int
    zone_id: int
    x_coord: int
    y_coord: int
    density_val: float
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Alert DTOs ---

class CrowdAlertCreate(BaseModel):
    alert_type: str
    severity: str = Field(..., pattern="^(Info|Warning|Critical)$")
    message: str

class CrowdAlertOut(BaseModel):
    id: int
    zone_id: int
    alert_type: str
    severity: str
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True
