from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.models.auth import Base

class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_type = Column(String(100), nullable=False)
    recommendation = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    priority = Column(String(50), nullable=False, default="Medium")
    reason = Column(Text, nullable=True)
    affected_services = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="Proposed") # Proposed, Accepted, Rejected
    explanation_id = Column(Integer, ForeignKey("ai_explanations.id", ondelete="SET NULL"), nullable=True)
    suggested_commands = Column(JSON, nullable=True) # list of command payloads to trigger in command center

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    explanation = relationship("AIExplanation", foreign_keys=[explanation_id])
    decisions = relationship("AIDecision", back_populates="recommendation", cascade="all, delete-orphan")
    feedbacks = relationship("AIFeedback", back_populates="recommendation", cascade="all, delete-orphan")
    references = relationship("AIKnowledgeReference", back_populates="recommendation", cascade="all, delete-orphan")


class AIRiskAssessment(Base):
    __tablename__ = "ai_risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    crowd_risk = Column(Float, default=0.0)
    medical_risk = Column(Float, default=0.0)
    security_risk = Column(Float, default=0.0)
    fire_risk = Column(Float, default=0.0)
    transit_risk = Column(Float, default=0.0)
    accessibility_risk = Column(Float, default=0.0)
    overall_risk = Column(Float, default=0.0)
    status = Column(String(50), nullable=False, default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    explanation = Column(Text, nullable=True)
    contributing_factors = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class AIExplanation(Base):
    __tablename__ = "ai_explanations"

    id = Column(Integer, primary_key=True, index=True)
    reason = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    related_events = Column(JSON, nullable=True)
    playbooks = Column(JSON, nullable=True)
    risks = Column(JSON, nullable=True)
    alternatives = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class AIDecision(Base):
    __tablename__ = "ai_decisions"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False)
    decision_type = Column(String(50), nullable=False) # ACCEPT, REJECT
    comment = Column(Text, nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    recommendation = relationship("AIRecommendation", back_populates="decisions")
    operator = relationship("User")


class AICorrelation(Base):
    __tablename__ = "ai_correlations"

    id = Column(Integer, primary_key=True, index=True)
    source_service = Column(String(100), nullable=False)
    target_service = Column(String(100), nullable=False)
    correlation_type = Column(String(100), nullable=False)
    strength = Column(Float, default=0.0)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class AIFeedback(Base):
    __tablename__ = "ai_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False) # 1-5 rating
    comments = Column(Text, nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    recommendation = relationship("AIRecommendation", back_populates="feedbacks")
    operator = relationship("User")


class AITimeline(Base):
    __tablename__ = "ai_timeline"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False) # RECOMMENDATION, RISK, DECISION
    event_type = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }


class AIAudit(Base):
    __tablename__ = "ai_audits"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    actor = relationship("User")


class AIKnowledgeReference(Base):
    __tablename__ = "ai_knowledge_references"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    citation_label = Column(String(255), nullable=False)
    reference_url = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    recommendation = relationship("AIRecommendation", back_populates="references")
    document = relationship("KnowledgeDocument")
