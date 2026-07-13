from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class PreferenceSave(BaseModel):
    theme: str = "dark"
    preferences: Optional[Dict[str, Any]] = None

class PreferenceOut(BaseModel):
    id: int
    user_id: int
    theme: str
    preferences: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class WidgetCreate(BaseModel):
    title: str
    status: str = "Active"
    priority: str = "Medium"
    widget_type: str
    config: Optional[Dict[str, Any]] = None

class WidgetOut(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    widget_type: str
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SnapshotCreate(BaseModel):
    snapshot_type: str
    data: Dict[str, Any]

class SnapshotOut(BaseModel):
    id: int
    snapshot_type: str
    data: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationOut(BaseModel):
    id: int
    level: str
    message: str
    is_dismissed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertOut(BaseModel):
    id: int
    alert_type: str
    source: str
    message: str
    severity: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimelineOut(BaseModel):
    id: int
    source_service: str
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
