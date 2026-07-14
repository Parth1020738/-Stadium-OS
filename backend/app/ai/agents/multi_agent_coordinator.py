import asyncio
import time
from typing import Dict, Any, List, Optional
from backend.app.ai.agents.agent_definitions import (
    CrowdAgent, IncidentAgent, TransitAgent, VolunteerAgent, AccessibilityAgent,
    SustainabilityAgent, SecurityAgent, MedicalAgent, WeatherAgent, CommandAgent
)
from backend.app.ai.agents.agent_memory import global_agent_memory

class MultiAgentCoordinator:
    def __init__(self, db: Optional[Any] = None):
        self.db = db
        self.agents = {
            "crowd": CrowdAgent(),
            "incident": IncidentAgent(),
            "transit": TransitAgent(),
            "volunteer": VolunteerAgent(),
            "accessibility": AccessibilityAgent(),
            "sustainability": SustainabilityAgent(),
            "security": SecurityAgent(),
            "medical": MedicalAgent(),
            "weather": WeatherAgent(),
            "command": CommandAgent()
        }

    async def generate_action_plan(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate all agents to generate a coordinated operational plan."""
        start_time = time.time()
        
        # 1. Add historical memory context
        mem_summary = global_agent_memory.get_context_summary()
        extended_context = {**context, "memory": mem_summary}

        # 2. Run all agents in parallel
        tasks = {}
        for name, agent in self.agents.items():
            tasks[name] = asyncio.create_task(agent.run(query, extended_context))

        results = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                # Safe fallback
                results[name] = {
                    "name": name.capitalize() + " Agent",
                    "summary": f"{name} analysis failed: {str(e)}",
                    "reasoning": "Error occurred during execution.",
                    "confidence": 0.5,
                    "recommended_actions": []
                }

        # 3. Cross-Agent Collaboration logic
        # Example: if Crowd Agent or Transit Agent has warnings, adapt other agents' context/decisions
        collab_logs = []
        crowd_rec = results["crowd"].get("recommended_actions", [])
        transit_rec = results["transit"].get("recommended_actions", [])

        if crowd_rec and any("gate d" in r.lower() for r in crowd_rec):
            collab_logs.append("Crowd Agent predicts congestion at Gate D -> Transit Agent triggers secondary shuttle support.")
            if "transit" in results and not results["transit"].get("recommended_actions"):
                results["transit"]["recommended_actions"] = ["Increase shuttle frequency for Gate D route by 20%"]
            
            collab_logs.append("Crowd Agent predicts congestion at Gate D -> Volunteer Agent schedules 5 stewards reallocation.")
            if "volunteer" in results and not results["volunteer"].get("recommended_actions"):
                results["volunteer"]["recommended_actions"] = ["Deploy Volunteer Team Bravo (5 stewards) to Gate D"]

        # 4. Conflict Resolution Strategy
        # Identify conflicts (e.g. Crowd wants Gate C open, Security or Transit wants Gate C closed)
        conflicts = []
        resolved_recommendation = None
        
        # Simulating/parsing conflict detection
        q_lower = query.lower()
        if "gate c" in q_lower or "emergency" in q_lower or "conflict" in q_lower:
            conflicts.append({
                "agent_a": "Crowd Agent",
                "recommendation_a": "Keep Gate C open to reduce evacuation time by 6 minutes.",
                "agent_b": "Transit Agent",
                "recommendation_b": "Close Gate C to restrict passenger flow to outer ring roads.",
                "resolution": "Safety override: Keep Gate C open. Restricting flow increases outer ring queue density by 18%."
            })
            resolved_recommendation = "Keep Gate C open with additional perimeter security guards."

        # 5. Build Timeline Plan (Autonomous Stadium Planning)
        timeline = []
        step_delta = 2 # step minutes
        current_minute = 0
        
        # Extract actions from all agents to form a cohesive timeline
        all_actions = []
        for name, res in results.items():
            recs = res.get("recommended_actions", [])
            for r in recs:
                if r not in all_actions:
                    all_actions.append((name, r))

        if not all_actions:
            # Fallback nominal timeline
            timeline = [
                {"time": "00:00", "action": "Verify turnstiles status", "agent": "Crowd Agent"},
                {"time": "00:05", "action": "Recalculate crowd density indicators", "agent": "Crowd Agent"}
            ]
        else:
            for agent_name, action in all_actions:
                timeline.append({
                    "time": f"00:{current_minute:02d}",
                    "action": action,
                    "agent": self.agents[agent_name].name
                })
                current_minute += step_delta

        # 6. Resource Optimization Recommendations
        resources = {
            "volunteers": "Nominal allocations active.",
            "security": "Nominal patrolling patterns.",
            "shuttles": "Operating on regular headway schedules."
        }
        
        if "gate d" in q_lower or "congest" in q_lower or "emergency" in q_lower:
            resources = {
                "volunteers": "Move 5 stewards from North Stand to Gate D bypass gates.",
                "security": "Deploy 4 perimeter guards to Gate D corridor.",
                "shuttles": "Stagger Metro departures and dispatch 2 standby buses.",
                "emergency_response": "Deploy First Aid Squad 4 to Sector B corridor."
            }

        # Calculate average confidence
        confidences = [res.get("confidence", 0.90) for res in results.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.90

        # Construct coordinated plan
        plan = {
            "query": query,
            "agents": results,
            "collaboration_logs": collab_logs,
            "conflicts": conflicts,
            "timeline": timeline,
            "resource_optimizations": resources,
            "confidence": round(avg_confidence, 2),
            "latency_ms": int((time.time() - start_time) * 1000)
        }

        # 7. Record to memory
        global_agent_memory.record_decision(query, plan)

        return plan

    def generate_briefings(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Compile executive briefing cards for various stadium officials based on the coordinator plan."""
        briefings = {}
        roles = ["ceo", "operations", "volunteer", "transit", "security", "medical", "accessibility", "sustainability"]
        
        for role in roles:
            briefings[role] = self._compile_role_briefing(role, plan)

        return briefings

    def _compile_role_briefing(self, role: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        agents = plan.get("agents", {})
        
        if role == "ceo":
            status = "Green"
            if plan.get("conflicts"):
                status = "Amber"
            return {
                "role_title": "Chief Executive Officer",
                "status": status,
                "summary": "Stadium ingress operations are running. Handled 1 coordinate planning request with no major safety hazards.",
                "predictions": "High egress flow expected post-match. Turnstile scanning speed remains stable.",
                "risks": "Gate C potential corridor bottleneck (mitigated by safety open override).",
                "recommended_actions": ["Approve operational timeline overrides for matchday exit flow."],
                "confidence": plan.get("confidence", 0.95)
            }
        elif role == "operations":
            return {
                "role_title": "Director of Operations",
                "status": "Green",
                "summary": "Matchday control center telemetry registers stable crowd flows.",
                "predictions": "Queue times at Gate D predicted to rise slightly under high volume.",
                "risks": "Minor shift overlap gaps for stewards.",
                "recommended_actions": [t["action"] for t in plan.get("timeline", [])[:3]],
                "confidence": plan.get("confidence", 0.92)
            }
        elif role == "volunteer":
            vol_res = agents.get("volunteer", {})
            return {
                "role_title": "Volunteer Coordinator",
                "status": "Green" if not vol_res.get("potential_risks") else "Amber",
                "summary": vol_res.get("summary", "Volunteer allocation nominal."),
                "predictions": "Roster compliance stable.",
                "risks": vol_res.get("potential_risks", ["Steward overlap lag."]),
                "recommended_actions": vol_res.get("recommended_actions", ["Monitor shift check-ins."]),
                "confidence": vol_res.get("confidence", 0.90)
            }
        elif role == "transit":
            transit_res = agents.get("transit", {})
            return {
                "role_title": "Transit Operations Lead",
                "status": "Green" if not transit_res.get("potential_risks") else "Amber",
                "summary": transit_res.get("summary", "Transit headways within threshold."),
                "predictions": "Shuttle capacity meets demand.",
                "risks": transit_res.get("potential_risks", ["Outer Ring Road delays."]),
                "recommended_actions": transit_res.get("recommended_actions", ["Maintain current loop intervals."]),
                "confidence": transit_res.get("confidence", 0.91)
            }
        elif role == "security":
            sec_res = agents.get("security", {})
            return {
                "role_title": "Security Commander",
                "status": "Green",
                "summary": sec_res.get("summary", "Gates and corridors fully secured."),
                "predictions": "No perimeter breaches detected.",
                "risks": sec_res.get("potential_risks", []),
                "recommended_actions": sec_res.get("recommended_actions", ["Regular perimeter patrols."]),
                "confidence": sec_res.get("confidence", 0.95)
            }
        elif role == "medical":
            med_res = agents.get("medical", {})
            return {
                "role_title": "Chief Medical Officer",
                "status": "Green",
                "summary": med_res.get("summary", "First aid rooms ready on standby."),
                "predictions": "Expected patient volume within nominal tolerances.",
                "risks": med_res.get("potential_risks", []),
                "recommended_actions": med_res.get("recommended_actions", ["Maintain medic standby sectors."]),
                "confidence": med_res.get("confidence", 0.94)
            }
        elif role == "accessibility":
            acc_res = agents.get("accessibility", {})
            return {
                "role_title": "Accessibility Specialist",
                "status": "Green" if not acc_res.get("potential_risks") else "Amber",
                "summary": acc_res.get("summary", "All vertical lifts running."),
                "predictions": "Ramps and elevators clear.",
                "risks": acc_res.get("potential_risks", []),
                "recommended_actions": acc_res.get("recommended_actions", []),
                "confidence": acc_res.get("confidence", 0.98)
            }
        else:
            sust_res = agents.get("sustainability", {})
            return {
                "role_title": "Sustainability Coordinator",
                "status": "Green",
                "summary": sust_res.get("summary", "Energy conservation measures online."),
                "predictions": "Solar storage load optimal.",
                "risks": sust_res.get("potential_risks", []),
                "recommended_actions": sust_res.get("recommended_actions", []),
                "confidence": sust_res.get("confidence", 0.92)
            }
