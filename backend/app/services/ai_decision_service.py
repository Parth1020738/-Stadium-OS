import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.core.kafka_producer import kafka_producer
from backend.app.core.redis import redis_manager

# Models
from backend.app.models.ai import (
    AIRecommendation, AIRiskAssessment, AIExplanation, AIDecision,
    AICorrelation, AIFeedback, AITimeline, AIAudit, AIKnowledgeReference
)
from backend.app.models.knowledge import KnowledgeDocument
from backend.app.models.incident import Incident
from backend.app.models.volunteer import Volunteer, VolunteerShift
from backend.app.models.transit import TransitTrip
from backend.app.models.accessibility import AccessibilityBarrier

# Repositories
from backend.app.repositories.ai_repository import (
    AIRecommendationRepository, AIRiskAssessmentRepository, AIExplanationRepository,
    AIDecisionRepository, AICorrelationRepository, AIFeedbackRepository,
    AITimelineRepository, AIAuditRepository, AIKnowledgeReferenceRepository
)
# Command center service integration
from backend.app.services.command_service import CommandGatewayService

logger = logging.getLogger("ai_decision_service")

class BaseAIService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rec_repo = AIRecommendationRepository(db)
        self.risk_repo = AIRiskAssessmentRepository(db)
        self.exp_repo = AIExplanationRepository(db)
        self.dec_repo = AIDecisionRepository(db)
        self.corr_repo = AICorrelationRepository(db)
        self.feed_repo = AIFeedbackRepository(db)
        self.time_repo = AITimelineRepository(db)
        self.audit_repo = AIAuditRepository(db)
        self.ref_repo = AIKnowledgeReferenceRepository(db)

    async def log_audit(self, actor_id: Optional[int], action: str, details: Optional[Dict[str, Any]] = None):
        audit = AIAudit(actor_id=actor_id, action=action, details=details)
        await self.audit_repo.create(audit)
        await self.db.commit()

    async def log_timeline(self, category: str, event_type: str, details: Optional[Dict[str, Any]] = None):
        item = AITimeline(category=category, event_type=event_type, details=details)
        await self.time_repo.create(item)
        await self.db.commit()
        # Publish
        await kafka_producer.send_event("ai.timeline.created", "current", {
            "category": category,
            "event_type": event_type,
            "details": details
        })


class RiskPredictionService(BaseAIService):
    async def get_latest_risk(self) -> AIRiskAssessment:
        latest = await self.risk_repo.get_latest()
        if latest:
            return latest
        # Fallback default
        return AIRiskAssessment(
            crowd_risk=10.0, medical_risk=5.0, security_risk=5.0,
            fire_risk=2.0, transit_risk=10.0, accessibility_risk=5.0,
            overall_risk=6.0, status="LOW", explanation="Default baseline risk nominal."
        )

    async def calculate_live_risk(self) -> AIRiskAssessment:
        # Check Redis density key
        density = await redis_manager.client.get("dashboard:metrics:average_density")
        density_val = float(density.decode("utf-8")) if density else 0.45

        # Check Redis active incidents count
        active_inc = await redis_manager.client.get("dashboard:metrics:active_incidents_count")
        inc_val = int(active_inc.decode("utf-8")) if active_inc else 0

        # Calculate scores
        crowd_risk = min(density_val * 100.0, 100.0)
        medical_risk = min(inc_val * 15.0, 100.0)
        security_risk = min(inc_val * 20.0, 100.0)
        fire_risk = 5.0
        transit_risk = 15.0
        accessibility_risk = 10.0

        overall_risk = (crowd_risk + medical_risk + security_risk + fire_risk + transit_risk + accessibility_risk) / 6.0
        status = "LOW"
        if overall_risk > 75.0:
            status = "CRITICAL"
        elif overall_risk > 50.0:
            status = "HIGH"
        elif overall_risk > 25.0:
            status = "MEDIUM"

        risk = AIRiskAssessment(
            crowd_risk=crowd_risk,
            medical_risk=medical_risk,
            security_risk=security_risk,
            fire_risk=fire_risk,
            transit_risk=transit_risk,
            accessibility_risk=accessibility_risk,
            overall_risk=overall_risk,
            status=status,
            explanation=f"Stadium overall risk score computed at {overall_risk:.1f}%. Major contributors: crowd flow and active incident counts.",
            contributing_factors={"crowd_density": density_val, "active_incidents": inc_val}
        )
        await self.risk_repo.create(risk)
        await self.db.commit()

        # Cache risk stats in Redis
        await redis_manager.client.setex("ai:latest_risk_score", 300, str(overall_risk))

        # Publish event
        await kafka_producer.send_event("ai.risk.updated", "overall", {
            "overall_risk": overall_risk,
            "status": status
        })
        await self.log_timeline("RISK", "RISK_CALCULATED", {"overall_risk": overall_risk, "status": status})

        return risk


class CrowdRecommendationEngine:
    def evaluate(self, density: float) -> Dict[str, Any]:
        if density > 0.8:
            return {
                "recommendation": "Gate rate override: open secondary exit gates to clear corridor overcrowding.",
                "confidence": 0.92,
                "priority": "High",
                "reason": f"Corridor density exceeded 80% (Current: {density:.2f})",
                "affected_services": ["Transit", "Accessibility"],
                "estimated_impact": "Corridor queue times reduced by 40%",
                "suggested_commands": [{"command_type": "GATE_RATE_OVERRIDE", "payload": {"gate_id": "Gate-A", "open_ratio": 1.0}}]
            }
        return {
            "recommendation": "Crowd flow nominal. Continue monitoring stadium corridors.",
            "confidence": 0.95,
            "priority": "Low",
            "reason": f"Corridor density nominal (Current: {density:.2f})",
            "affected_services": [],
            "estimated_impact": "N/A",
            "suggested_commands": []
        }


class IncidentRecommendationEngine:
    def evaluate(self, incident_count: int) -> Dict[str, Any]:
        if incident_count > 3:
            return {
                "recommendation": "Dispatch standby volunteer stewards to active incident sectors to assist security teams.",
                "confidence": 0.88,
                "priority": "Medium",
                "reason": f"Multiple active incidents detected ({incident_count} open incidents)",
                "affected_services": ["Volunteer", "Incident"],
                "estimated_impact": "Volunteer response dispatch lag reduced by 5 minutes",
                "suggested_commands": []
            }
        return {
            "recommendation": "Active incidents count nominal.",
            "confidence": 0.95,
            "priority": "Low",
            "reason": "Active incidents nominal",
            "affected_services": [],
            "estimated_impact": "N/A",
            "suggested_commands": []
        }


class EvacuationRecommendationEngine:
    def evaluate(self, overall_risk: float) -> Dict[str, Any]:
        if overall_risk > 75.0:
            return {
                "recommendation": "Initiate evacuation warning for South Corridor due to critical stadium congestion.",
                "confidence": 0.98,
                "priority": "Critical",
                "reason": f"Stadium overall risk critical ({overall_risk:.1f}%)",
                "affected_services": ["Transit", "Accessibility", "Incident"],
                "estimated_impact": "Complete South Corridor clearance within 12 minutes",
                "suggested_commands": [{"command_type": "EMERGENCY_EVACUATION", "payload": {"zone": "South Corridor"}}]
            }
        return {
            "recommendation": "Evacuation path clear. No evacuation required.",
            "confidence": 0.99,
            "priority": "Low",
            "reason": "Stadium overall risk stable",
            "affected_services": [],
            "estimated_impact": "N/A",
            "suggested_commands": []
        }


class AIDecisionService(BaseAIService):
    async def get_overview(self) -> Dict[str, Any]:
        risk_service = RiskPredictionService(self.db)
        risk = await risk_service.get_latest_risk()
        recs = await self.rec_repo.list_recommendations(limit=5)
        timeline = await self.time_repo.list_timeline(limit=5)

        return {
            "risk_status": risk.status,
            "overall_risk_score": risk.overall_risk,
            "recent_recommendations_count": len(recs),
            "timeline_length": len(timeline)
        }

    async def get_recommendation(self, rec_id: int) -> Optional[AIRecommendation]:
        return await self.rec_repo.get_by_id(rec_id)

    async def get_all_recommendations(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[AIRecommendation]:
        return await self.rec_repo.list_recommendations(limit=limit, offset=offset, status=status)

    async def generate_recommendations(self) -> List[AIRecommendation]:
        # Gather live values from Redis
        density = await redis_manager.client.get("dashboard:metrics:average_density")
        density_val = float(density.decode("utf-8")) if density else 0.45

        active_inc = await redis_manager.client.get("dashboard:metrics:active_incidents_count")
        inc_val = int(active_inc.decode("utf-8")) if active_inc else 0

        risk_service = RiskPredictionService(self.db)
        risk = await risk_service.get_latest_risk()

        engines = [
            CrowdRecommendationEngine().evaluate(density_val),
            IncidentRecommendationEngine().evaluate(inc_val),
            EvacuationRecommendationEngine().evaluate(risk.overall_risk)
        ]

        created_recs = []
        for eng in engines:
            # Only save non-low recommendations to prevent spamming
            if eng["priority"] != "Low":
                # RAG playbook matching from Knowledge Service
                playbook_title = "Standard Operating Procedure"
                citation_label = "SOP-1"
                stmt = select(KnowledgeDocument).where(
                    KnowledgeDocument.title.contains("Evacuation") | KnowledgeDocument.content.contains("Crowd"),
                    KnowledgeDocument.is_deleted == False
                ).limit(1)
                res_doc = await self.db.execute(stmt)
                doc = res_doc.scalar_one_or_none()
                if doc:
                    playbook_title = doc.title
                    citation_label = f"DOC-{doc.id}"

                explanation = AIExplanation(
                    reason=eng["reason"],
                    evidence=f"Computed indicators show correlation between density={density_val} and open incidents={inc_val}.",
                    confidence=eng["confidence"],
                    related_events={"density": density_val, "incidents": inc_val},
                    playbooks=[playbook_title],
                    risks=["Corridor gridlock", "Operator delay"],
                    alternatives=["Increase steward guidance patrol"]
                )
                await self.exp_repo.create(explanation)
                await self.db.flush()

                rec = AIRecommendation(
                    recommendation_type=eng["affected_services"][0] if eng["affected_services"] else "System",
                    recommendation=eng["recommendation"],
                    confidence=eng["confidence"],
                    priority=eng["priority"],
                    reason=eng["reason"],
                    affected_services=eng["affected_services"],
                    status="Proposed",
                    explanation_id=explanation.id,
                    suggested_commands=eng["suggested_commands"]
                )
                await self.rec_repo.create(rec)
                await self.db.flush()

                # Add knowledge citation reference if document exists
                if doc:
                    ref = AIKnowledgeReference(
                        recommendation_id=rec.id,
                        document_id=doc.id,
                        citation_label=citation_label,
                        reference_url=f"/api/v1/documents/{doc.id}"
                    )
                    await self.ref_repo.create(ref)
                
                created_recs.append(rec)

                # Publish Kafka event
                await kafka_producer.send_event("ai.recommendation.created", str(rec.id), {
                    "id": rec.id,
                    "priority": rec.priority,
                    "recommendation": rec.recommendation
                })
                await self.log_timeline("RECOMMENDATION", "RECOMMENDATION_CREATED", {"id": rec.id, "priority": rec.priority})

        await self.db.commit()
        return created_recs

    async def accept_recommendation(self, rec_id: int, user_id: int) -> Optional[AIRecommendation]:
        rec = await self.rec_repo.get_by_id(rec_id)
        if rec and rec.status == "Proposed":
            rec.status = "Accepted"
            
            # Record decision
            decision = AIDecision(recommendation_id=rec_id, decision_type="ACCEPT", operator_id=user_id)
            await self.dec_repo.create(decision)
            
            # Central Command Gateway integration: execute suggested commands
            if rec.suggested_commands:
                cmd_service = CommandGatewayService(self.db)
                for cmd_data in rec.suggested_commands:
                    await cmd_service.submit_command(
                        command_type=cmd_data["command_type"],
                        payload=cmd_data["payload"],
                        creator_id=user_id
                    )

            await self.db.commit()

            # Publish event
            await kafka_producer.send_event("ai.recommendation.accepted", str(rec_id), {
                "id": rec_id,
                "operator_id": user_id
            })
            await self.log_timeline("DECISION", "RECOMMENDATION_ACCEPTED", {"id": rec_id, "user_id": user_id})

            return rec
        return None

    async def reject_recommendation(self, rec_id: int, user_id: int, comment: Optional[str] = None) -> Optional[AIRecommendation]:
        rec = await self.rec_repo.get_by_id(rec_id)
        if rec and rec.status == "Proposed":
            rec.status = "Rejected"

            decision = AIDecision(recommendation_id=rec_id, decision_type="REJECT", comment=comment, operator_id=user_id)
            await self.dec_repo.create(decision)
            await self.db.commit()

            # Publish event
            await kafka_producer.send_event("ai.recommendation.rejected", str(rec_id), {
                "id": rec_id,
                "operator_id": user_id,
                "comment": comment
            })
            await self.log_timeline("DECISION", "RECOMMENDATION_REJECTED", {"id": rec_id, "user_id": user_id})

            return rec
        return None

    async def save_feedback(self, rec_id: int, rating: int, comments: Optional[str], user_id: int) -> AIFeedback:
        fb = AIFeedback(recommendation_id=rec_id, rating=rating, comments=comments, operator_id=user_id)
        await self.feed_repo.create(fb)
        await self.db.commit()
        await self.log_timeline("FEEDBACK", "FEEDBACK_SUBMITTED", {"recommendation_id": rec_id, "rating": rating})
        return fb
