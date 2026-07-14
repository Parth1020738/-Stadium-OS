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
        
        # Pull details from corresponding agent if available, else use default values
        agent_data = agents.get(role, {}) or agents.get("crowd", {})
        
        # Standard default fallbacks that are overwritten per role
        current_situation = "Stadium operations are running at nominal flow. Ingress rate is balanced."
        major_risks = "No major risks identified at this time."
        current_incidents = "Zero active critical incidents."
        ai_recommendations = ["Continue standard dashboard monitoring."]
        expected_problems = "Possible egress transit surge."
        resource_status = "Staffing and volunteers at 100% check-in rate."
        priority_actions = ["Monitor gate turnstiles."]
        confidence = plan.get("confidence", 0.95)
        reasoning = "System telemetry reports regular traffic flow across all sectors."

        if role == "ceo":
            current_situation = "Stadium ingress operations are active for FIFA World Cup Matchday. Flow is stable."
            major_risks = "Potential egress corridor bottleneck if Gate C is prematurely restricted."
            current_incidents = "1 minor slip and fall, 1 elevator technical warning."
            ai_recommendations = ["Approve Gate C safety override to maintain open status.", "Deploy additional stewards to elevator lobby."]
            expected_problems = "Egress surge immediately following final whistle."
            resource_status = "Volunteer stewards: 45 active, Security patrols: 15 active, Medical: 4 squads active."
            priority_actions = ["Authorize gate rate overrides for matchday exit flow."]
            reasoning = "Ensures ingress/egress safety metrics stay within the 6-minute threshold."
        elif role == "operations":
            current_situation = "Control center monitors stable crowd flows and optimal vehicle headways."
            major_risks = "Queue congestion at Gate D bypass."
            current_incidents = "Minor delay on outer ring shuttle route."
            ai_recommendations = ["Increase Metro Shuttle frequency.", "Stagger turnstile scanning gates if density spikes."]
            expected_problems = "Elevator mechanical failure near Gate C."
            resource_status = "Shuttles active: 12, standby vehicles: 2."
            priority_actions = ["Deploy Volunteer Team Bravo to assist Gate D flow."]
            reasoning = "Ingress rates match ticket scanning capacities; no critical bottlenecks detected."
        elif role == "security":
            sec_res = agents.get("security", {})
            current_situation = sec_res.get("summary", "Gates and corridors fully secured.")
            major_risks = "Unapproved access points near Gate C outer perimeter."
            current_incidents = sec_res.get("potential_risks", ["Steward allocation gap."])
            ai_recommendations = sec_res.get("recommended_actions", ["Regular perimeter patrols."])
            expected_problems = "Crowd surge near ticketing checkpoints."
            resource_status = "Security Personnel: 45 guards on shift, 5 supervisors."
            priority_actions = ["Increase security patrols at Gate C perimeter."]
            confidence = sec_res.get("confidence", 0.95)
            reasoning = sec_res.get("reasoning", "CCTV feed analytics show no unauthorized activity.")
        elif role == "volunteer":
            vol_res = agents.get("volunteer", {})
            current_situation = vol_res.get("summary", "Volunteer allocation nominal.")
            major_risks = "South Stand (Zone 5) steward check-in delay."
            current_incidents = vol_res.get("potential_risks", ["Steward overlap lag."])
            ai_recommendations = vol_res.get("recommended_actions", ["Deploy Team Bravo."])
            expected_problems = "Shift transition delays."
            resource_status = "Active stewards: 45, standby stewards: 10."
            priority_actions = ["Trigger push notification to standby stewards."]
            confidence = vol_res.get("confidence", 0.90)
            reasoning = vol_res.get("reasoning", "Volunteer check-in records indicate 92% attendance.")
        elif role == "transit":
            transit_res = agents.get("transit", {})
            current_situation = transit_res.get("summary", "Transit headways within threshold.")
            major_risks = "Metro Shuttle junction delays due to traffic."
            current_incidents = transit_res.get("potential_risks", ["Outer Ring Road delays."])
            ai_recommendations = transit_res.get("recommended_actions", ["Deploy standby buses."])
            expected_problems = "Passenger queue growth at station hub."
            resource_status = "Buses running: 12, standby: 3."
            priority_actions = ["Increase Metro Shuttle frequency by deploying standby buses."]
            confidence = transit_res.get("confidence", 0.91)
            reasoning = transit_res.get("reasoning", "GPS tracking shows traffic bottleneck at Outer Ring junction.")
        elif role == "medical":
            med_res = agents.get("medical", {})
            current_situation = med_res.get("summary", "First aid rooms ready on standby.")
            major_risks = "Heat exhaustion cases in South Stand."
            current_incidents = med_res.get("potential_risks", [])
            ai_recommendations = med_res.get("recommended_actions", ["Maintain medic standby sectors."])
            expected_problems = "Dizziness incidents in unshaded rows."
            resource_status = "Paramedics: 8, First Aid Rooms active: 4."
            priority_actions = ["Dispatch First Aid Squad 4 to Sector B."]
            confidence = med_res.get("confidence", 0.94)
            reasoning = med_res.get("reasoning", "High ambient temperatures correlate with rising heat exhaustion logs.")
        elif role == "accessibility":
            acc_res = agents.get("accessibility", {})
            current_situation = acc_res.get("summary", "All vertical lifts running.")
            major_risks = "Ramp B wheelchair bottleneck."
            current_incidents = acc_res.get("potential_risks", [])
            ai_recommendations = acc_res.get("recommended_actions", ["Redirect wheelchair guests to Elevator 1."])
            expected_problems = "Mechanical failure of elevator 2 near Gate C."
            resource_status = "Elevators operational: 6/6, ramps clear: 100%."
            priority_actions = ["Deploy 2 stewards to Gate C lift to assist manually."]
            confidence = acc_res.get("confidence", 0.98)
            reasoning = acc_res.get("reasoning", "Elevator E-204 telemetry indicates normal mechanical door function.")
        elif role == "sustainability":
            sust_res = agents.get("sustainability", {})
            current_situation = sust_res.get("summary", "Energy conservation measures online.")
            major_risks = "Halftime suit temperature peaks."
            current_incidents = sust_res.get("potential_risks", [])
            ai_recommendations = sust_res.get("recommended_actions", ["Approve halftime energy setbacks."])
            expected_problems = "Solar generation drop due to rain/overcast."
            resource_status = "Solar production: 420 kW, Waste diversion teams active."
            priority_actions = ["Set HVAC target to 23C in VIP suites."]
            confidence = sust_res.get("confidence", 0.92)
            reasoning = sust_res.get("reasoning", "Smart HVAC setback maintains suit thermal comfort while reducing grid loads.")

        return {
            "role_title": role.upper() + " Executive Briefing",
            "current_situation": current_situation,
            "major_risks": major_risks,
            "current_incidents": current_incidents,
            "ai_recommendations": ai_recommendations,
            "expected_problems": expected_problems,
            "resource_status": resource_status,
            "priority_actions": priority_actions,
            "confidence": confidence,
            "reasoning": reasoning
        }

