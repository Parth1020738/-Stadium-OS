from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List, Any

# --- Shared Base Responses ---
class UserMinimalOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True

class SkillMinimalOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

# --- Requests ---
class CreateVolunteerRequest(BaseModel):
    user_id: int
    team_id: Optional[int] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    email: EmailStr
    preferred_language: Optional[str] = "en"
    bio: Optional[str] = None

class UpdateVolunteerRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    preferred_language: Optional[str] = None
    bio: Optional[str] = None

class CreateShiftRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location_zone: str = Field(..., min_length=1, max_length=100)
    required_skills: Optional[str] = None

class AssignShiftRequest(BaseModel):
    volunteer_id: int

class CheckInRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None

class CheckOutRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None

class CreateSkillRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class AssignSkillRequest(BaseModel):
    skill_id: int
    proficiency_level: str = Field("Intermediate", pattern="^(Beginner|Intermediate|Expert)$")

class AddCertificationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    issuing_authority: str = Field(..., min_length=1, max_length=150)
    license_number: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None

class AddAvailabilityRequest(BaseModel):
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: str = Field(..., pattern="^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern="^\d{2}:\d{2}$")
    specific_date: Optional[datetime] = None

class UpdateLocationRequest(BaseModel):
    latitude: float
    longitude: float

# --- Responses ---
class VolunteerProfileResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: Optional[str]
    email: str
    preferred_language: str
    bio: Optional[str]

    class Config:
        from_attributes = True

class VolunteerTeamResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    lead_id: Optional[int]

    class Config:
        from_attributes = True

class VolunteerResponse(BaseModel):
    id: int
    user_id: int
    team_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    profile: Optional[VolunteerProfileResponse] = None
    team: Optional[VolunteerTeamResponse] = None

    class Config:
        from_attributes = True

class ShiftResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location_zone: str
    required_skills: Optional[str]
    status: str
    version_id: int

    class Config:
        from_attributes = True

class AssignmentResponse(BaseModel):
    id: int
    shift_id: int
    volunteer_id: int
    status: str
    created_at: datetime
    shift: Optional[ShiftResponse] = None

    class Config:
        from_attributes = True

class AttendanceResponse(BaseModel):
    id: int
    assignment_id: int
    status: str
    checked_in_at: Optional[datetime]
    checked_out_at: Optional[datetime]

    class Config:
        from_attributes = True

class StatisticsResponse(BaseModel):
    total_volunteers: int
    active_volunteers: int
    on_shift_volunteers: int
    total_shifts: int
    completed_shifts: int
    attendance_rate: float

class PaginationResponse(BaseModel):
    total: int
    limit: int
    offset: int
    results: List[Any]

class ErrorResponse(BaseModel):
    error: str
    details: Optional[dict] = None
