from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class CommandCreate(BaseModel):
    command_type: str
    payload: Optional[Dict[str, Any]] = None

class CommandApprovalAction(BaseModel):
    comments: Optional[str] = None

class CommandOut(BaseModel):
    id: int
    command_type: str
    payload: Optional[Dict[str, Any]] = None
    status: str
    correlation_id: str
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    version_id: int

    class Config:
        from_attributes = True

class CommandApprovalOut(BaseModel):
    id: int
    command_id: int
    approver_id: Optional[int] = None
    status: str
    comments: Optional[str] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
