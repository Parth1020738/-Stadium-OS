from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from backend.app.models.ai import (
    AIRecommendation, AIRiskAssessment, AIExplanation, AIDecision,
    AICorrelation, AIFeedback, AITimeline, AIAudit, AIKnowledgeReference
)

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def commit(self):
        await self.db.commit()

    async def flush(self):
        await self.db.flush()


class AIRecommendationRepository(BaseRepository):
    async def get_by_id(self, rec_id: int) -> Optional[AIRecommendation]:
        stmt = select(AIRecommendation).where(
            AIRecommendation.id == rec_id,
            AIRecommendation.is_deleted == False
        ).options(
            selectinload(AIRecommendation.explanation),
            selectinload(AIRecommendation.decisions),
            selectinload(AIRecommendation.feedbacks),
            selectinload(AIRecommendation.references)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_recommendations(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[AIRecommendation]:
        stmt = select(AIRecommendation).where(AIRecommendation.is_deleted == False).options(
            selectinload(AIRecommendation.explanation),
            selectinload(AIRecommendation.decisions),
            selectinload(AIRecommendation.feedbacks),
            selectinload(AIRecommendation.references)
        )
        if status:
            stmt = stmt.where(AIRecommendation.status == status)
        stmt = stmt.order_by(AIRecommendation.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, rec: AIRecommendation) -> AIRecommendation:
        self.db.add(rec)
        return rec


class AIRiskAssessmentRepository(BaseRepository):
    async def get_latest(self) -> Optional[AIRiskAssessment]:
        stmt = select(AIRiskAssessment).where(
            AIRiskAssessment.is_deleted == False
        ).order_by(AIRiskAssessment.created_at.desc()).limit(1)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, risk: AIRiskAssessment) -> AIRiskAssessment:
        self.db.add(risk)
        return risk


class AIExplanationRepository(BaseRepository):
    async def create(self, exp: AIExplanation) -> AIExplanation:
        self.db.add(exp)
        return exp


class AIDecisionRepository(BaseRepository):
    async def create(self, dec: AIDecision) -> AIDecision:
        self.db.add(dec)
        return dec


class AICorrelationRepository(BaseRepository):
    async def list_correlations(self, limit: int = 50) -> List[AICorrelation]:
        stmt = select(AICorrelation).where(AICorrelation.is_deleted == False).order_by(AICorrelation.created_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, corr: AICorrelation) -> AICorrelation:
        self.db.add(corr)
        return corr


class AIFeedbackRepository(BaseRepository):
    async def create(self, feedback: AIFeedback) -> AIFeedback:
        self.db.add(feedback)
        return feedback


class AITimelineRepository(BaseRepository):
    async def list_timeline(self, limit: int = 50) -> List[AITimeline]:
        stmt = select(AITimeline).where(AITimeline.is_deleted == False).order_by(AITimeline.created_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, timeline: AITimeline) -> AITimeline:
        self.db.add(timeline)
        return timeline


class AIAuditRepository(BaseRepository):
    async def create(self, audit: AIAudit) -> AIAudit:
        self.db.add(audit)
        return audit


class AIKnowledgeReferenceRepository(BaseRepository):
    async def create(self, ref: AIKnowledgeReference) -> AIKnowledgeReference:
        self.db.add(ref)
        return ref
