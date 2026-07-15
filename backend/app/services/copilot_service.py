import logging
import asyncio
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from backend.app.models.knowledge import KnowledgeDocument
from backend.app.models.incident import Incident
from backend.app.core.config import settings

logger = logging.getLogger("copilot_service")

class AICopilotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def answer_operator_query(self, query: str) -> Dict[str, Any]:
        if settings.ENABLE_MOCK_AI:
            await asyncio.sleep(0.4) # Simulate LLM inference delay
            
        query_lower = query.lower()
        
        # Base structure
        res = {
            "response": "Query received. Seeking relevant stadium playbooks and incidents logs context...",
            "confidence": 0.90,
            "references": ["Knowledge-Base-General"],
            "summary": "General operations inquiry.",
            "reasoning": "Determined via baseline sensor verification.",
            "timeline": [
                {"time": "00:00", "action": "Assess query context", "agent": "System Agent"},
                {"time": "00:05", "action": "Verify database indicators", "agent": "System Agent"}
            ],
            "affected_areas": ["All Gates"],
            "departments": ["Operations Center"],
            "commands": [],
            "alternative_plans": ["Continue regular dashboard sweep."],
            "risk": "Minimal operational risk.",
            "resources_needed": [],
            "expected_outcome": "Maintain regular monitoring schedule."
        }

        # 1. "What is happening?" or general status
        if "happening" in query_lower or "status" in query_lower:
            res.update({
                "response": "Stadium operations are currently nominal. Crowd levels are stable across all gates.",
                "confidence": 0.96,
                "summary": "Stadium ingress operations are within safe threshold parameters.",
                "reasoning": "Sensors report balanced ingress rates and zero active blockages.",
                "affected_areas": ["All Gates", "Concourses"],
                "departments": ["Crowd Management", "Command Center"],
                "risk": "Low. Turnstile processing times are averaging under 45 seconds.",
                "expected_outcome": "Optimal crowd ingress flow is maintained."
            })

        # 2. "What should I do?" or recommendations
        elif "do" in query_lower or "action" in query_lower:
            res.update({
                "response": "Review active recommendations in the dashboard. South Gate rate override is recommended to reduce incoming queue times.",
                "confidence": 0.91,
                "summary": "High ingress rate detected. Recommended secondary gates opening.",
                "reasoning": "Ingress rate (85 people/min) is exceeding gate capacity.",
                "timeline": [
                    {"time": "00:00", "action": "Alert Gate D supervisor", "agent": "Crowd Agent"},
                    {"time": "00:02", "action": "Dispatch volunteer team Bravo", "agent": "Volunteer Agent"}
                ],
                "affected_areas": ["South Gate", "Gate D"],
                "departments": ["Crowd Management", "Volunteer Service"],
                "commands": ["Open Gate D", "Dispatch Volunteer Team"],
                "alternative_plans": ["Stagger arrivals using transit shuttle holds."],
                "risk": "High crowd density (exceeding 3.5 people/sqm) if ignored.",
                "resources_needed": ["5 volunteers", "Gate D keys"],
                "expected_outcome": "South Gate density reduced by 25% within 10 minutes."
            })

        # 3. "Show highest priority incidents"
        elif "incidents" in query_lower or "priority" in query_lower:
            res.update({
                "response": "Currently tracking 1 high-priority incident: Security alert in Gate 3 corridor.",
                "confidence": 0.94,
                "summary": "Security alert in Zone 3 corridor requires immediate attention.",
                "reasoning": "Intrusion warning triggered on CCTV sensor 12.",
                "affected_areas": ["Zone 3 Corridor"],
                "departments": ["Security Control"],
                "commands": ["Increase Security Patrol"],
                "alternative_plans": ["Lock down Zone 3 corridor access points."],
                "risk": "Unauthorized guest ingress into secure player zones.",
                "resources_needed": ["4 security guards"],
                "expected_outcome": "Perimeter re-secured and cleared within 4 minutes."
            })

        # 4. "Why is Gate A congested?"
        elif "gate a" in query_lower or "congested" in query_lower:
            res.update({
                "response": "Gate A congestion is driven by high egress transit shuttle delays combined with single-file ADA queue restrictions.",
                "confidence": 0.93,
                "summary": "Gate A queue length has increased to 120 guests.",
                "reasoning": "Shuttle delay has paused passenger boarding, creating a queue backup.",
                "affected_areas": ["Gate A Bypass", "Transit Hub"],
                "departments": ["Transit Control", "Accessibility Service"],
                "commands": ["Increase Shuttle Frequency"],
                "alternative_plans": ["Redirect non-ADA guests to Ramp C."],
                "risk": "Elevated customer frustration and minor queue crush hazard.",
                "resources_needed": ["2 standby shuttles"],
                "expected_outcome": "Queue length halved within 7 minutes."
            })

        # 5. "Recommend volunteer deployment" or deployment
        elif "volunteer" in query_lower or "deployment" in query_lower:
            res.update({
                "response": "Recommended: Deploy 3 volunteer stewards to Ramp Corridor 2 to assist with crowd flow redirection.",
                "confidence": 0.89,
                "summary": "Steward allocation shortfall in Zone 2.",
                "reasoning": "Ramp 2 ingress flow has increased by 35% in the last 10 minutes.",
                "affected_areas": ["Ramp Corridor 2"],
                "departments": ["Volunteer Service"],
                "commands": ["Dispatch Volunteer Team"],
                "alternative_plans": ["Display static digital directional indicators."],
                "risk": "Localized bottleneck on Ramp 2 stairs.",
                "resources_needed": ["3 volunteers"],
                "expected_outcome": "Redirection reduces ramp occupancy density to normal parameters.",
                "data": {
                    "deployment": {
                        "stewards_count": 3
                    }
                }
            })

        # 6. "Best evacuation path?" or evacuation
        elif "evacuation" in query_lower or "path" in query_lower:
            res.update({
                "response": "The safest evacuation path from South Arena is through Gate C. Gate A and South gate are currently showing high crowd density.",
                "confidence": 0.98,
                "summary": "South Arena evacuation plan activated.",
                "reasoning": "Gate C is closest with lowest crowd density metrics.",
                "affected_areas": ["South Arena", "Gate C Route"],
                "departments": ["Emergency Response", "Command Center"],
                "commands": ["Open Gate", "Broadcast Announcement"],
                "alternative_plans": ["Route evacuation through Gate E."],
                "risk": "Evacuation delay if guests attempt to exit through Gate A.",
                "resources_needed": ["All active security personnel", "Public Address system"],
                "expected_outcome": "South Arena cleared safely within 9 minutes."
            })

        # 7. "Nearest medical team?" or medical
        elif "medical" in query_lower or "team" in query_lower:
            res.update({
                "response": "Nearest medical team (First Aid Squad 4) is located at Sector B. Current transit time is less than 3 minutes.",
                "confidence": 0.95,
                "summary": "Medical response dispatch for row 14 dizzy guest.",
                "reasoning": "Heat exhaustion warning triggered via supervisor mobile log.",
                "affected_areas": ["Sector B, Row 14"],
                "departments": ["Medical Service"],
                "commands": ["Increase Medical Staff"],
                "alternative_plans": ["Dispatch adjacent volunteer with water and first aid kit."],
                "risk": "Severe heatstroke if medical care is delayed.",
                "resources_needed": ["First Aid Squad 4", "Cold water packs"],
                "expected_outcome": "Guest stabilized on-site within 3 minutes."
            })

        return res

