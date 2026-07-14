import logging
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.incident import Incident
from backend.app.models.crowd import CrowdSnapshot
from backend.app.models.transit import TransitDelay, TransitRoute
from backend.app.models.volunteer import Volunteer
from backend.app.models.command import Command
from backend.app.models.ai import AITimeline, AIRecommendation, AIExplanation
from backend.app.core.redis import redis_manager
from backend.app.core.kafka_producer import kafka_producer

logger = logging.getLogger("demo_mode_service")

class DemoModeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def trigger_scenario(self, scenario_name: str) -> dict:
        """Trigger simulated events,Telemetry,Incidents,Commands and Timeline updates in the DB and Redis."""
        logger.info(f"Simulating scenario: {scenario_name}")
        
        # 1. Update general Redis telemetry keys
        await redis_manager.client.set("dashboard:metrics:average_density", "0.85" if scenario_name in ["crowd_surge", "evacuation"] else "0.45")
        
        timestamp = datetime.utcnow()
        incident_id = None
        command_id = None
        details = f"Simulated scenario {scenario_name} successfully initiated."

        if scenario_name == "crowd_surge":
            # Ingress crowd surge simulation
            # 1. Create a crowd snapshot
            snapshot = CrowdSnapshot(
                total_count=78420,
                average_density=0.88,
                flow_rate=95.0,
                velocity=1.2,
                confidence_score=0.97,
                timestamp=timestamp
            )
            self.db.add(snapshot)
            
            # 2. Create Incident
            inc = Incident(
                title="Crowd Surge Bottleneck at Gate D",
                description="Ingress crowd accumulation near Gate D turnstiles has caused turnstile scans density to rise above 0.8 people/sqm.",
                severity="High",
                priority="High",
                category="CrowdControl",
                status="Open",
                location_zone="Gate D",
                location_details="Turnstile outer entrance corridor",
                created_at=timestamp
            )
            self.db.add(inc)
            await self.db.flush()
            incident_id = inc.id

            # 3. Create Command in DB (Pending status, requires RBAC approval)
            cmd = Command(
                command_type="GATE_RATE_OVERRIDE",
                payload={"gate_id": "Gate-D", "open_ratio": 1.0, "reason": "Crowd surge mitigation"},
                status="Pending",
                correlation_id=f"corr-{uuid.uuid4()}",
                created_at=timestamp
            )
            self.db.add(cmd)
            await self.db.flush()
            command_id = cmd.id

        elif scenario_name == "lost_child":
            inc = Incident(
                title="Lost Child Report - Sector B Row 8",
                description="Operator report of an 8-year-old child separated from family near Sector B ticketing box.",
                severity="Medium",
                priority="Medium",
                category="Security",
                status="Open",
                location_zone="Sector B",
                location_details="Ticketing Box Corridor B",
                created_at=timestamp
            )
            self.db.add(inc)
            await self.db.flush()
            incident_id = inc.id

            cmd = Command(
                command_type="BROADCAST_ANNOUNCEMENT",
                payload={"announcement_text": "Paging lost child in Sector B. Stewards deploy to exits.", "target_zones": ["Sector B", "Gate C"]},
                status="Pending",
                correlation_id=f"corr-{uuid.uuid4()}",
                created_at=timestamp
            )
            self.db.add(cmd)
            await self.db.flush()
            command_id = cmd.id

        elif scenario_name == "medical_emergency":
            inc = Incident(
                title="Medical Emergency - Heart Attack Warning Sector C",
                description="Guest in Sector C Row 14 reporting chest pain. First aid squad dispatch required immediately.",
                severity="Critical",
                priority="Critical",
                category="Medical",
                status="Open",
                location_zone="Sector C",
                location_details="Row 14 Seat 10",
                created_at=timestamp
            )
            self.db.add(inc)
            await self.db.flush()
            incident_id = inc.id

            cmd = Command(
                command_type="INCREASE_MEDICAL_STAFF",
                payload={"medic_team": "First Aid Squad 4", "dispatch_location": "Sector C"},
                status="Pending",
                correlation_id=f"corr-{uuid.uuid4()}",
                created_at=timestamp
            )
            self.db.add(cmd)
            await self.db.flush()
            command_id = cmd.id

        elif scenario_name == "power_outage":
            inc = Incident(
                title="Partial Power Outage - North Stand Concourse",
                description="Section 4 Lighting loop offline. Standby generators running at 100% capacity.",
                severity="High",
                priority="Critical",
                category="Facility",
                status="Open",
                location_zone="North Stand",
                location_details="Concourse section 4",
                created_at=timestamp
            )
            self.db.add(inc)
            await self.db.flush()
            incident_id = inc.id

            cmd = Command(
                command_type="ACTIVATE_ACCESSIBILITY_ROUTE",
                payload={"route_id": "Emergency-Backup-North", "activate": True},
                status="Pending",
                correlation_id=f"corr-{uuid.uuid4()}",
                created_at=timestamp
            )
            self.db.add(cmd)
            await self.db.flush()
            command_id = cmd.id

        elif scenario_name == "heavy_rain":
            inc = Incident(
                title="Heavy Rain Storm Warning",
                description="National weather service advisory indicates heavy downpour starting in 5 minutes. High risk of slipping on open ramps.",
                severity="Medium",
                priority="Medium",
                category="Weather",
                status="Open",
                location_zone="Stadium Ramps",
                location_details="All outdoor vertical ramps",
                created_at=timestamp
            )
            self.db.add(inc)
            await self.db.flush()
            incident_id = inc.id

            cmd = Command(
                command_type="BROADCAST_ANNOUNCEMENT",
                payload={"announcement_text": "Attention: Ramps may be slippery due to rain. Please proceed with caution.", "target_zones": ["All Concourses"]},
                status="Pending",
                correlation_id=f"corr-{uuid.uuid4()}",
                created_at=timestamp
            )
            self.db.add(cmd)
            await self.db.flush()
            command_id = cmd.id

        elif scenario_name == "vip_arrival":
            inc = Incident(
                title="VIP Escort Route Clearing - Gate 3",
                description="High-profile delegation arriving via Gate 3 VIP terminal. Secure escort required.",
                severity="Low",
                priority="Medium",
                category="Security",
                status="Open",
                location_zone="Gate 3 VIP",
                location_details="VIP access road",
                created_at=timestamp
            )
            self.db.add(inc)
            await self.db.flush()
            incident_id = inc.id

            cmd = Command(
                command_type="INCREASE_SECURITY_PATROL",
                payload={"patrol_id": "VIP-Escort-Bravo", "zone": "Gate 3 VIP"},
                status="Pending",
                correlation_id=f"corr-{uuid.uuid4()}",
                created_at=timestamp
            )
            self.db.add(cmd)
            await self.db.flush()
            command_id = cmd.id

        elif scenario_name == "transport_delay":
            # 1. Create transit delay
            delay = TransitDelay(
                reason="Traffic congestion at Outer Ring Road junction",
                estimated_delay_minutes=15,
                reported_at=timestamp
            )
            self.db.add(delay)
            
            inc = Incident(
                title="Metro Shuttle Service Delay - Route B",
                description="Shuttle bus headway has risen to 22 minutes due to severe congestion at Outer Ring road junction.",
                severity="High",
                priority="High",
                category="Transit",
                status="Open",
                location_zone="Transit Route B",
                location_details="Outer Ring Road",
                created_at=timestamp
            )
            self.db.add(inc)
            await self.db.flush()
            incident_id = inc.id

            cmd = Command(
                command_type="INCREASE_SHUTTLE_FREQUENCY",
                payload={"route_id": "Route-B", "buses_to_add": 2},
                status="Pending",
                correlation_id=f"corr-{uuid.uuid4()}",
                created_at=timestamp
            )
            self.db.add(cmd)
            await self.db.flush()
            command_id = cmd.id

        elif scenario_name == "security_alert":
            inc = Incident(
                title="Ticketing Counter Breach Attempt - Gate C",
                description="Unidentified guest attempting to bypass ticketing validator scanning boundary at Gate C.",
                severity="High",
                priority="High",
                category="Security",
                status="Open",
                location_zone="Gate C Perimeter",
                location_details="Ticketing Box Counter 4",
                created_at=timestamp
            )
            self.db.add(inc)
            await self.db.flush()
            incident_id = inc.id

            cmd = Command(
                command_type="INCREASE_SECURITY_PATROL",
                payload={"guards_count": 4, "target_location": "Gate C Perimeter"},
                status="Pending",
                correlation_id=f"corr-{uuid.uuid4()}",
                created_at=timestamp
            )
            self.db.add(cmd)
            await self.db.flush()
            command_id = cmd.id

        # 4. Save AITimeline entry
        timeline_item = AITimeline(
            category="SIMULATION",
            event_type="SCENARIO_TRIGGERED",
            details={
                "scenario": scenario_name,
                "timestamp": timestamp.isoformat(),
                "incident_id": incident_id,
                "command_id": command_id
            },
            created_at=timestamp
        )
        self.db.add(timeline_item)
        
        # 5. Commit all DB changes
        await self.db.commit()

        # 6. Publish Event via Kafka
        await kafka_producer.send_event("ai.simulation.triggered", scenario_name, {
            "scenario": scenario_name,
            "incident_id": incident_id,
            "command_id": command_id,
            "timestamp": timestamp.isoformat()
        })

        return {
            "scenario": scenario_name,
            "status": "SUCCESS",
            "incident_id": incident_id,
            "command_id": command_id,
            "details": details
        }
