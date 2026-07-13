from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class CopilotQueryRequest(BaseModel):
    query: str

class CopilotQueryResponse(BaseModel):
    response: str
    confidence: float
    references: List[str]
    data: Optional[Dict[str, Any]] = None


class FeedbackCreate(BaseModel):
    recommendation_id: int
    rating: int # 1 to 5
    comments: Optional[str] = None

class FeedbackOut(BaseModel):
    id: int
    recommendation_id: int
    rating: int
    comments: Optional[str] = None
    operator_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExplanationOut(BaseModel):
    id: int
    reason: str
    evidence: Optional[str] = None
    confidence: float
    related_events: Optional[Dict[str, Any]] = None
    playbooks: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    alternatives: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationOut(BaseModel):
    id: int
    recommendation_type: str
    recommendation: str
    confidence: float
    priority: str
    reason: Optional[str] = None
    affected_services: Optional[List[str]] = None
    status: str
    explanation_id: Optional[int] = None
    suggested_commands: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime
    explanation: Optional[ExplanationOut] = None

    model_config = ConfigDict(from_attributes=True)


class RiskAssessmentOut(BaseModel):
    id: int
    crowd_risk: float
    medical_risk: float
    security_risk: float
    fire_risk: float
    transit_risk: float
    accessibility_risk: float
    overall_risk: float
    status: str
    explanation: Optional[str] = None
    contributing_factors: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimelineOut(BaseModel):
    id: int
    category: str
    event_type: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
