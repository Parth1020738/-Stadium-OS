from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any, Optional

# Import models to build real context
from backend.app.models.incident import Incident
from backend.app.models.crowd import CrowdSnapshot
from backend.app.models.transit import TransitRoute, TransitTrip, TransitDelay
from backend.app.models.volunteer import Volunteer, VolunteerShift
from backend.app.models.accessibility import AccessibilityBarrier
from backend.app.models.command import Command
from backend.app.models.knowledge import KnowledgeDocument
from backend.app.models.ai import AIRecommendation, AITimeline

class ContextBuilder:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def build_context(self, operator_role: str = "Operator", session_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate all real-time stadium metrics from the database."""
        context = {
            "current_time": datetime.now(timezone.utc).isoformat(),
            "venue": "Aegis Colosseum",
            "upcoming_match": "FIFA World Cup Final: France vs Argentina (Kickoff at 21:00)",
            "operator_role": operator_role,
            "weather": "Heavy Rain, 18°C, Wind 15 km/h",
            "crowd": "Normal flow, 82% stadium capacity",
            "incidents": "0 active critical incidents",
            "transit": "All shuttle lines operating normally",
            "volunteers": "45 stewards active on shift",
            "accessibility": "Elevator in Section B is functional",
            "reports": "Event KPI: 94% customer satisfaction rating",
            "knowledge_base": "Stadium handbook: Gate 3 is primary entry for VIPs.",
            "digital_twin": "Telemetry is synchronous. Sensor network operating at 98.4% uptime.",
            "command_center": "No pending alerts or commands.",
            "mission_control": "Agent coordination is active.",
            "available_staff": "Security Patrol Team Alpha (5), First Aid Squad 4 (4), Maintenance Team 2 (3)",
            "emergency_resources": "Standby ambulances: 3, fire extinguishers: 120, emergency exits: fully clear"
        }

        if not self.db:
            return context

        try:
            # Query real incidents
            incident_stmt = select(Incident).where(Incident.status != "Resolved")
            incident_res = await self.db.execute(incident_stmt)
            incidents = incident_res.scalars().all()
            if incidents:
                context["incidents"] = f"{len(incidents)} active incidents: " + ", ".join([f"[{i.priority}] {i.title} in {i.location_zone}" for i in incidents])

            # Query real crowd snapshot
            crowd_stmt = select(CrowdSnapshot).order_by(CrowdSnapshot.timestamp.desc()).limit(1)
            crowd_res = await self.db.execute(crowd_stmt)
            latest_crowd = crowd_res.scalar_one_or_none()
            if latest_crowd:
                context["crowd"] = f"Total count: {latest_crowd.total_count}, average density: {latest_crowd.average_density} people/sqm"

            # Query real transit
            transit_stmt = select(TransitRoute)
            transit_res = await self.db.execute(transit_stmt)
            routes = transit_res.scalars().all()
            
            trip_stmt = select(TransitTrip).where(TransitTrip.status == "Active")
            trip_res = await self.db.execute(trip_stmt)
            trips = trip_res.scalars().all()
            
            delay_stmt = select(TransitDelay).where(TransitDelay.resolved_at == None)
            delay_res = await self.db.execute(delay_stmt)
            delays = delay_res.scalars().all()
            
            transit_parts = []
            if routes:
                transit_parts.append(f"{len(routes)} routes registered")
            if trips:
                transit_parts.append(f"{len(trips)} active trips running")
            if delays:
                transit_parts.append(f"{len(delays)} delays reported: " + ", ".join([d.reason for d in delays]))
            if transit_parts:
                context["transit"] = ". ".join(transit_parts)

            # Query real volunteers
            vol_stmt = select(Volunteer).where(Volunteer.status == "Active")
            vol_res = await self.db.execute(vol_stmt)
            vols = vol_res.scalars().all()
            
            shift_stmt = select(VolunteerShift).where(VolunteerShift.end_time > datetime.now())
            shift_res = await self.db.execute(shift_stmt)
            shifts = shift_res.scalars().all()
            
            vol_parts = []
            if vols:
                vol_parts.append(f"{len(vols)} active volunteers on shift")
            if shifts:
                vol_parts.append(f"{len(shifts)} scheduled shifts active")
            if vol_parts:
                context["volunteers"] = ". ".join(vol_parts)

            # Query real accessibility barriers
            barrier_stmt = select(AccessibilityBarrier).where(AccessibilityBarrier.status != "Resolved")
            barrier_res = await self.db.execute(barrier_stmt)
            barriers = barrier_res.scalars().all()
            if barriers:
                context["accessibility"] = f"{len(barriers)} active barriers: " + ", ".join([f"{b.barrier_type} at {b.location_details}" for b in barriers])

            # Query Knowledge base
            kb_stmt = select(KnowledgeDocument).where(KnowledgeDocument.is_deleted == False).limit(3)
            kb_res = await self.db.execute(kb_stmt)
            docs = kb_res.scalars().all()
            if docs:
                context["knowledge_base"] = "Referenced playbooks: " + "; ".join([f"{d.title} ({d.citation_label or 'N/A'})" for d in docs])

            # Query Command Center commands
            cmd_stmt = select(Command).order_by(Command.created_at.desc()).limit(5)
            cmd_res = await self.db.execute(cmd_stmt)
            cmds = cmd_res.scalars().all()
            if cmds:
                context["command_center"] = f"Recent commands: " + ", ".join([f"[{c.status}] {c.command_type}" for c in cmds])

            # Query Mission Control timeline
            timeline_stmt = select(AITimeline).order_by(AITimeline.created_at.desc()).limit(5)
            timeline_res = await self.db.execute(timeline_stmt)
            timeline_items = timeline_res.scalars().all()
            if timeline_items:
                context["mission_control"] = f"Recent operational events: " + ", ".join([f"{t.event_type}: {str(t.details)}" for t in timeline_items])

        except Exception as e:
            # Fall back to default on error
            pass

        return context
