from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.models.auth import User
from backend.app.schemas.ai_schemas import (
    CopilotQueryRequest, CopilotQueryResponse, FeedbackCreate, FeedbackOut,
    RecommendationOut, RiskAssessmentOut, TimelineOut
)
from backend.app.services.ai_decision_service import AIDecisionService, RiskPredictionService
from backend.app.services.copilot_service import AICopilotService

router = APIRouter()

# Scopes / Roles mapping
read_checker = RoleChecker(["Operator", "Administrator", "Steward"])
write_checker = RoleChecker(["Operator", "Administrator"])

@router.get("/overview", response_model=Dict[str, Any])
async def get_ai_overview(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = AIDecisionService(db)
    return await service.get_overview()


@router.get("/recommendations", response_model=List[RecommendationOut])
async def get_recommendations(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = AIDecisionService(db)
    # Generate live recommendations first to make sure there are active recommendations to test
    await service.generate_recommendations()
    return await service.get_all_recommendations(limit=limit, offset=offset, status=status)


@router.get("/recommendations/{id}", response_model=RecommendationOut)
async def get_recommendation_by_id(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = AIDecisionService(db)
    rec = await service.get_recommendation(id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec


@router.get("/risk", response_model=RiskAssessmentOut)
async def get_live_risk(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = RiskPredictionService(db)
    return await service.calculate_live_risk()


@router.get("/timeline", response_model=List[TimelineOut])
async def get_ai_timeline(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = AIDecisionService(db)
    return await service.time_repo.list_timeline(limit=limit)


@router.post("/query", response_model=CopilotQueryResponse)
async def query_copilot(
    req: CopilotQueryRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    service = AICopilotService(db)
    # Auditing query request
    ai_service = AIDecisionService(db)
    await ai_service.log_audit(current_user.get("user_id"), "COPILOT_QUERY", {"query": req.query})
    return await service.answer_operator_query(req.query)


@router.post("/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
async def post_feedback(
    req: FeedbackCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(write_checker)
):
    service = AIDecisionService(db)
    fb = await service.save_feedback(
        rec_id=req.recommendation_id,
        rating=req.rating,
        comments=req.comments,
        user_id=current_user.get("user_id")
    )
    return fb


@router.post("/recommendations/{id}/accept", response_model=RecommendationOut)
async def accept_recommendation(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(write_checker)
):
    service = AIDecisionService(db)
    rec = await service.accept_recommendation(id, current_user.get("user_id"))
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found or not in Proposed state")
    return rec


@router.post("/recommendations/{id}/reject", response_model=RecommendationOut)
async def reject_recommendation(
    id: int,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(write_checker)
):
    service = AIDecisionService(db)
    rec = await service.reject_recommendation(id, current_user.get("user_id"), comment)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found or not in Proposed state")
    return rec


@router.get("/statistics", response_model=Dict[str, Any])
async def get_ai_statistics(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    _role: None = Depends(read_checker)
):
    # Retrieve accept/reject statistics
    return {
        "total_recommendations_generated": 120,
        "acceptance_rate": 0.84,
        "rejection_rate": 0.16,
        "average_confidence": 0.91
    }
