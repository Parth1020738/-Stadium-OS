from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    role: str
    content: str

class AIChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = None

class AIChatResponse(BaseModel):
    response: str
    session_id: str
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0

class AISummarizeRequest(BaseModel):
    text: str
    max_length: Optional[int] = 500

class AISummarizeResponse(BaseModel):
    summary: str
    tokens_used: int = 0

class AIRecommendRequest(BaseModel):
    scenario: str
    parameters: Optional[Dict[str, Any]] = None

class RecommendationItem(BaseModel):
    title: str
    description: str
    confidence: float
    priority: str

class AIRecommendResponse(BaseModel):
    recommendations: List[RecommendationItem]
    confidence_score: float

class AIExplainRequest(BaseModel):
    code_or_data: str
    topic: Optional[str] = None

class AIExplainResponse(BaseModel):
    explanation: str
    complexity: str

class AITranslateRequest(BaseModel):
    text: str
    target_language: str

class AITranslateResponse(BaseModel):
    translated_text: str
    source_language: str

class AIBriefingRequest(BaseModel):
    scope: str = "stadium"

class AIBriefingResponse(BaseModel):
    briefing: str
    sections: Dict[str, Any]
    timestamp: str

class AICopilotRequest(BaseModel):
    query: str

class AICopilotResponse(BaseModel):
    answer: str
    suggested_commands: List[str] = []
    tokens_used: int = 0
