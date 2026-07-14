import os
import json
from typing import Dict, Any, List, Optional
from backend.app.ai.gemini_service import GeminiService
from backend.app.ai.prompt_manager import PromptManager

class BaseAgent:
    def __init__(self, name: str, prompt_file: str, gemini_service: Optional[GeminiService] = None):
        self.name = name
        self.prompt_file = prompt_file
        self.gemini = gemini_service or GeminiService()
        self.prompt_manager = PromptManager()

    async def run(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent reasoning using Gemini or a customized domain mock."""
        # 1. Load specialized prompt template
        variables = {**context, "query": query}
        try:
            domain_prompt = self.prompt_manager.load_prompt(self.prompt_file, variables)
        except Exception:
            # Fallback simple template
            domain_prompt = f"Agent: {self.name}\nContext: {str(context)}\nQuery: {query}"

        system_instruction = f"You are the {self.name} Agent for Aegis Smart Stadium OS. Provide a structured JSON response matching the required schema."

        if self.gemini.enable_mock:
            return self.get_mock_response(query, context)

        try:
            response_text = await self.gemini.generate_content(domain_prompt, system_instruction, json_mode=True)
            return json.loads(response_text)
        except Exception as e:
            # Safe fallback JSON
            return self.get_mock_response(query, context)

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Overridden by subclasses
        return {
            "name": self.name,
            "summary": f"{self.name} analysis complete.",
            "reasoning": "Using nominal baseline configurations.",
            "confidence": 0.90,
            "recommended_actions": [],
            "alternative_actions": [],
            "potential_risks": [],
            "expected_impact": "Nominal operations maintained."
        }

class CrowdAgent(BaseAgent):
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Crowd Agent", "crowd", gemini_service)

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "gate d" in q_lower or "congest" in q_lower or "surge" in q_lower or "emergency" in q_lower:
            return {
                "name": self.name,
                "summary": "Gate D turnstiles are experiencing a 42% bottleneck, increasing queue times to 15 minutes.",
                "reasoning": "Real-time ticket validation rates (48 scans/min) are lower than the ingress arrivals rate (68 guests/min).",
                "confidence": 0.94,
                "recommended_actions": ["Open Gate D secondary bypass gates", "Activate digital signage rerouting to Gate E"],
                "alternative_actions": ["Implement minor security hold to stagger arrivals", "Bypass VIP turnstile validations for pre-screened guests"],
                "potential_risks": ["Crowd density exceeds 4.2 people/sqm", "Ticket scanner failure cascade"],
                "expected_impact": "Reduces queue density by 22% within 5 minutes.",
                "resource_allocations": {"gate_opening": "Gate D secondary", "volunteers_requested": 5}
            }
        return {
            "name": self.name,
            "summary": "Crowd flow is nominal across all primary zones (Average density: 1.8 people/sqm).",
            "reasoning": "Ingress ticket validation is balanced; no queue times exceed 4 minutes.",
            "confidence": 0.96,
            "recommended_actions": [],
            "alternative_actions": ["Monitor Gate A ingress as kickoff approaches"],
            "potential_risks": [],
            "expected_impact": "Flow remains optimal."
        }

class IncidentAgent(BaseAgent):
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Incident Agent", "incident", gemini_service)

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "leak" in q_lower or "incident" in q_lower or "emergency" in q_lower:
            return {
                "name": self.name,
                "summary": "Water leak in Zone 3 corridor near restroom 3B has caused a slipping hazard.",
                "reasoning": "Facility sensors reported water pressure drops; steward mobile dispatch confirmed standing water.",
                "confidence": 0.96,
                "recommended_actions": ["Deploy maintenance team to shut off valve 3B", "Redirect nearby crowd away from Corridor 3"],
                "alternative_actions": ["Close restroom 3B temporarily", "Place warning signs at corridor entry points"],
                "potential_risks": ["Guest slip-and-fall injuries", "Structural damage to corridor flooring"],
                "expected_impact": "Resolves water flow hazard in 12 minutes.",
                "resource_allocations": {"maintenance_deployed": 1, "warning_signs": 4}
            }
        return {
            "name": self.name,
            "summary": "No active high-priority incidents reported in the stadium queue.",
            "reasoning": "All dispatcher logs and facilities telemetry confirm normal operational parameters.",
            "confidence": 0.98,
            "recommended_actions": [],
            "alternative_actions": [],
            "potential_risks": [],
            "expected_impact": "Operations nominal."
        }

class TransitAgent(BaseAgent):
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Transit Agent", "transit", gemini_service)

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "transit" in q_lower or "shuttle" in q_lower or "delay" in q_lower or "emergency" in q_lower:
            return {
                "name": self.name,
                "summary": "Metro Shuttle line is experiencing a 10-minute delay due to traffic at the Outer Ring junction.",
                "reasoning": "GPS telemetry from shuttle units 4 & 5 indicates average speed has dropped to 12 km/h.",
                "confidence": 0.91,
                "recommended_actions": ["Increase Metro Shuttle frequency by deploying 2 standby buses", "Post delay alerts on digital transit screens"],
                "alternative_actions": ["Stagger metro arrivals by coordinating station entry gates", "Promote walking route C for fit passengers"],
                "potential_risks": ["Crowd accumulation at Metro Station Hub", "Passenger frustration leading to ingress delays"],
                "expected_impact": "Increases passenger transport capacity by 200 people/hour.",
                "resource_allocations": {"shuttles_deployed": 2, "transit_screens_updated": True}
            }
        return {
            "name": self.name,
            "summary": "Transit lines (Metro and Express shuttles) are running at optimal frequencies.",
            "reasoning": "Headway timing is stable at 5.5 minutes; average shuttle speed is 32 km/h.",
            "confidence": 0.95,
            "recommended_actions": [],
            "alternative_actions": [],
            "potential_risks": [],
            "expected_impact": "Transit capacity meets guest demand."
        }

class VolunteerAgent(BaseAgent):
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Volunteer Agent", "volunteer", gemini_service)

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "volunteer" in q_lower or "shortage" in q_lower or "steward" in q_lower or "emergency" in q_lower:
            return {
                "name": self.name,
                "summary": "South Stand (Zone 5) is underallocated by 5 volunteer stewards due to shift check-in delays.",
                "reasoning": "Roster allocation data shows 8 scheduled stewards vs 3 checked-in at Zone 5.",
                "confidence": 0.89,
                "recommended_actions": ["Dispatch Volunteer Team Bravo (5 stewards) from North Stand to South Stand", "Trigger push notification to standby stewards"],
                "alternative_actions": ["Reassign 3 gate stewards from Zone 1 to Zone 5", "Extend previous shift volunteers by 30 minutes"],
                "potential_risks": ["Turnstile management bottlenecks", "Volunteer exhaustion"],
                "expected_impact": "Fills the staff gap within 8 minutes, stabilizing turnstile management.",
                "resource_allocations": {"volunteers_reallocated": 5, "target_zone": "South Stand"}
            }
        return {
            "name": self.name,
            "summary": "Volunteer allocations are 100% compliant with matchday deployment plans.",
            "reasoning": "All 45 stewards are checked in and assigned to their respective sectors.",
            "confidence": 0.97,
            "recommended_actions": [],
            "alternative_actions": [],
            "potential_risks": [],
            "expected_impact": "Staffing levels are sufficient."
        }

class AccessibilityAgent(BaseAgent):
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Accessibility Agent", "accessibility", gemini_service)

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "accessibility" in q_lower or "elevator" in q_lower or "barrier" in q_lower or "emergency" in q_lower:
            return {
                "name": self.name,
                "summary": "Elevator 2 near Gate C is temporarily out of service (Mechanical door lock fault).",
                "reasoning": "Elevator telemetry logged fault code E-204 at 15:42; maintenance technician dispatched.",
                "confidence": 0.98,
                "recommended_actions": ["Redirect wheelchair guests to Elevator 1 via Ramp B", "Deploy 2 stewards to Gate C lift to assist manually"],
                "alternative_actions": ["Provide accessible shuttle transfer from Gate C to Gate A entry", "Escort guests through VIP elevator corridor"],
                "potential_risks": ["Wheelchair bottleneck on Ramp B", "Long elevator wait times exceeding 12 minutes"],
                "expected_impact": "Maintains ADA compliance and ensures continuous vertical mobility.",
                "resource_allocations": {"volunteers_deployed": 2, "alternative_route_active": "Ramp B"}
            }
        return {
            "name": self.name,
            "summary": "All 6 stadium elevators and ADA ramps are fully functional.",
            "reasoning": "IoT telemetry logs verify elevator doors and motors are performing within tolerances.",
            "confidence": 0.99,
            "recommended_actions": [],
            "alternative_actions": [],
            "potential_risks": [],
            "expected_impact": "ADA routing is unimpeded."
        }

class SustainabilityAgent(BaseAgent):
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Sustainability Agent", "executive", gemini_service) # Reuse executive prompt or default

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "energy" in q_lower or "lighting" in q_lower or "sustainability" in q_lower or "waste" in q_lower:
            return {
                "name": self.name,
                "summary": "Halftime migration allows a 15% reduction in main stadium lighting brightness.",
                "reasoning": "Guests leaving seats reduces direct field lighting demands; grid power optimization target reached.",
                "confidence": 0.92,
                "recommended_actions": ["Implement Halftime energy setbacks in non-critical corridors", "Set HVAC target to 23C in VIP suites"],
                "alternative_actions": ["Turn off secondary video screens during halftime", "Stagger escalator standby operation rates"],
                "potential_risks": ["Slightly reduced visibility in outer ring stairwells", "Suite temperature rises above comfort zone"],
                "expected_impact": "Saves 180 kWh of energy over the 15-minute halftime interval.",
                "resource_allocations": {"lighting_setback_pct": 15, "hvac_temp_target": 23}
            }
        return {
            "name": self.name,
            "summary": "Sustainability status is nominal. Solar generation is meeting 22% of current base load.",
            "reasoning": "Weather is clear; solar arrays are producing 420 kW; waste diversion teams are active.",
            "confidence": 0.94,
            "recommended_actions": [],
            "alternative_actions": [],
            "potential_risks": [],
            "expected_impact": "Carbon footprint targets are on track."
        }

class SecurityAgent(BaseAgent):
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Security Agent", "command_center", gemini_service)

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "gate" in q_lower or "emergency" in q_lower or "security" in q_lower or "crowd" in q_lower:
            return {
                "name": self.name,
                "summary": "Closing Gate C to incoming traffic is requested by Transit, but Crowd requires it open to prevent egress bottleneck.",
                "reasoning": "Safety guidelines dictate maintaining open gates during crowd egress to prevent stampedes.",
                "confidence": 0.95,
                "recommended_actions": ["Keep Gate C open to ingress/egress", "Increase security patrols at Gate C perimeter"],
                "alternative_actions": ["Keep Gate C partially open with active lane guides", "Establish emergency overflow zone inside perimeter"],
                "potential_risks": ["Crowd density spike at Gate C outer perimeter", "Perimeter breach if security counts drop"],
                "expected_impact": "Keeps crowd evacuation time within the safe 6-minute threshold.",
                "resource_allocations": {"security_redistributed": 4, "gate_state": "Open"}
            }
        return {
            "name": self.name,
            "summary": "Stadium perimeter and gates are fully secure.",
            "reasoning": "CCTV feeds and card reader access logs report zero breaches or unauthorized accesses.",
            "confidence": 0.97,
            "recommended_actions": [],
            "alternative_actions": [],
            "potential_risks": [],
            "expected_impact": "Perimeter safety intact."
        }

class MedicalAgent(BaseAgent):
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Medical Agent", "incident", gemini_service)

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "medical" in q_lower or "injury" in q_lower or "emergency" in q_lower:
            return {
                "name": self.name,
                "summary": "Minor medical issue reported at Sector B (Heat exhaustion / guest dizzy).",
                "reasoning": "Steward reported dizzy guest on row 14; dispatch logged request for assistance.",
                "confidence": 0.94,
                "recommended_actions": ["Dispatch First Aid Squad 4 to Sector B", "Provide cold water and ice pack"],
                "alternative_actions": ["Reroute nearby wheelchair steward to assist escort", "Request standby ambulance placement at Gate B"],
                "potential_risks": ["Delayed response time if Sector B corridors are crowded", "Guest fainting leading to minor concussion"],
                "expected_impact": "On-site care within 3 minutes; guest stabilized.",
                "resource_allocations": {"medical_team_deployed": "First Aid Squad 4", "eta_seconds": 180}
            }
        return {
            "name": self.name,
            "summary": "Medical teams are fully staffed and on standby. No critical issues reported.",
            "reasoning": "First aid rooms 1-4 are active; paramedics are on-site.",
            "confidence": 0.96,
            "recommended_actions": [],
            "alternative_actions": [],
            "potential_risks": [],
            "expected_impact": "Medical safety coverage at 100%."
        }

class WeatherAgent(BaseAgent):
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Weather Agent", "system", gemini_service)

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "weather" in q_lower or "rain" in q_lower or "storm" in q_lower or "emergency" in q_lower:
            return {
                "name": self.name,
                "summary": "Incoming rain shower predicted to begin in 15 minutes.",
                "reasoning": "Doppler radar update indicates precipitation band approaching from South-West.",
                "confidence": 0.90,
                "recommended_actions": ["Reroute volunteers to dry concourses", "Activate warning signs about wet flooring"],
                "alternative_actions": ["Deploy canopy extensions over Gate D/C queuing lines", "Suggest guests hold in covered concourses"],
                "potential_risks": ["Wet ramp slip hazards", "Sudden migration from open seating areas to concourses"],
                "expected_impact": "Preempts crowd rush, maintains dry paths.",
                "resource_allocations": {"warning_signs_active": True}
            }
        return {
            "name": self.name,
            "summary": "Weather is clear, 24°C, Wind 5 km/h. No changes expected.",
            "reasoning": "National weather service feeds indicate zero rain probability during match window.",
            "confidence": 0.98,
            "recommended_actions": [],
            "alternative_actions": [],
            "potential_risks": [],
            "expected_impact": "No weather-related operational impacts."
        }

class CommandAgent(BaseAgent):
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Command Agent", "command_center", gemini_service)

    def get_mock_response(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "gate d" in q_lower or "open" in q_lower or "shuttle" in q_lower or "emergency" in q_lower:
            return {
                "name": self.name,
                "summary": "Command execution prepared: Open Gate D and Dispatch Volunteers.",
                "reasoning": "Operator requested actionable steps; commands match playbook authorization codes.",
                "confidence": 0.97,
                "recommended_actions": ["Queue command 'Open Gate D' in command center", "Queue command 'Dispatch Volunteers' for Team Bravo"],
                "alternative_actions": ["Manual override toggle via physical command key", "Request verbal authorization from Operations Commander"],
                "potential_risks": ["Command execution logging delay", "Turnstile motor failure"],
                "expected_impact": "Enables RBAC command authorization flow.",
                "resource_allocations": {"queued_commands": ["Open Gate D", "Dispatch Volunteers"]}
            }
        return {
            "name": self.name,
            "summary": "No commands are currently queued for execution.",
            "reasoning": "System is in normal monitoring state.",
            "confidence": 0.95,
            "recommended_actions": [],
            "alternative_actions": [],
            "potential_risks": [],
            "expected_impact": "System remains in standby."
        }
