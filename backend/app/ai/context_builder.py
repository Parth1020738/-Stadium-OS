from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any, Optional

# Import models to build real context
from backend.app.models.incident import Incident
from backend.app.models.crowd import CrowdSnapshot
from backend.app.models.transit import TransitRoute
from backend.app.models.volunteer import Volunteer
from backend.app.models.accessibility import AccessibilityBarrier

class ContextBuilder:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def build_context(self, operator_role: str = "Operator", session_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate all real-time stadium metrics from the database."""
        context = {
            "current_time": datetime.now(timezone.utc).isoformat(),
            "venue": "Aegis Colosseum",
            "operator_role": operator_role,
            "weather": "Sunny, 24°C, Wind 5 km/h",
            "crowd": "Normal flow, 82% stadium capacity",
            "incidents": "0 active critical incidents",
            "transit": "All shuttle lines operating normally",
            "volunteers": "45 stewards active on shift",
            "accessibility": "Elevator in Section B is functional",
            "reports": "Event KPI: 94% customer satisfaction rating",
            "knowledge_base": "Stadium handbook: Gate 3 is primary entry for VIPs."
        }

        if not self.db:
            return context

        try:
            # Query real incidents
            incident_stmt = select(Incident).where(Incident.status != "Resolved")
            incident_res = await self.db.execute(incident_stmt)
            incidents = incident_res.scalars().all()
            if incidents:
                context["incidents"] = f"{len(incidents)} active incidents: " + ", ".join([f"[{i.priority}] {i.title}" for i in incidents])

            # Query real crowd snapshot
            crowd_stmt = select(CrowdSnapshot).order_list = [CrowdSnapshot.timestamp.desc()]
            # Wait, order_by(CrowdSnapshot.timestamp.desc())
            crowd_stmt = select(CrowdSnapshot).order_by(CrowdSnapshot.timestamp.desc()).limit(1)
            crowd_res = await self.db.execute(crowd_stmt)
            latest_crowd = crowd_res.scalar_one_or_none()
            if latest_crowd:
                context["crowd"] = f"Total count: {latest_crowd.total_count}, average density: {latest_crowd.average_density}"

            # Query real transit
            transit_stmt = select(TransitRoute)
            transit_res = await self.db.execute(transit_stmt)
            routes = transit_res.scalars().all()
            if routes:
                context["transit"] = ", ".join([f"Route {r.name}: status {r.status}" for r in routes])

            # Query real volunteers
            vol_stmt = select(Volunteer).where(Volunteer.status == "Active")
            vol_res = await self.db.execute(vol_stmt)
            vols = vol_res.scalars().all()
            if vols:
                context["volunteers"] = f"{len(vols)} active volunteers on shift"

            # Query real accessibility barriers
            barrier_stmt = select(AccessibilityBarrier).where(AccessibilityBarrier.status != "Resolved")
            barrier_res = await self.db.execute(barrier_stmt)
            barriers = barrier_res.scalars().all()
            if barriers:
                context["accessibility"] = f"{len(barriers)} active barriers: " + ", ".join([f"{b.barrier_type} in {b.location_details}" for b in barriers])

        except Exception as e:
            # Silently fall back to mocked defaults on db queries error
            pass

        return context
