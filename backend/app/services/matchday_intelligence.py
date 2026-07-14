import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger("matchday_intelligence")

class MatchdayModeService:
    _current_mode = "Pre Match" # Pre Match, Kickoff, Halftime, Full Time, Emergency Mode, Evacuation Mode

    @classmethod
    def get_current_mode(cls) -> str:
        return cls._current_mode

    @classmethod
    def set_mode(cls, mode: str):
        if mode in ["Pre Match", "Kickoff", "Halftime", "Full Time", "Emergency Mode", "Evacuation Mode"]:
            cls._current_mode = mode
            logger.info(f"Matchday intelligence mode shifted to: {mode}")
        else:
            raise ValueError(f"Invalid Matchday Mode: {mode}")

    @classmethod
    def get_mode_configurations(cls) -> Dict[str, Any]:
        mode = cls._current_mode
        if mode == "Pre Match":
            return {
                "ai_priority": "Ingress and Ticketing Queue Management",
                "recommended_actions": [
                    "Deploy volunteers to outer perimeter gates.",
                    "Optimize transit shuttle frequency for arrival lines.",
                    "Coordinate parking updates to digital signages."
                ],
                "resource_distribution": {
                    "volunteers": "South Stands & Main Ticketing Corridor",
                    "security": "External Perimeter Gates A, B & C",
                    "medical": "First Aid Rooms 1 & 2"
                },
                "expected_flow": "Incoming heavy traffic peak."
            }
        elif mode == "Kickoff":
            return {
                "ai_priority": "Corridor Density Minimization & Late Ingress Clearing",
                "recommended_actions": [
                    "Open secondary turnstile bypass gates.",
                    "Set main video screens to show seating access maps.",
                    "Monitor security cameras for perimeter breach."
                ],
                "resource_distribution": {
                    "volunteers": "Main Ingress Turnstiles",
                    "security": "Seating access stairs",
                    "medical": "All 4 First Aid Stations"
                },
                "expected_flow": "High density at gates, fast migration to seats."
            }
        elif mode == "Halftime":
            return {
                "ai_priority": "Concourse Flow Coordination & Energy/HVAC Setback Optimization",
                "recommended_actions": [
                    "Activate energy setbacks (HVAC to 23C in suites, light drop).",
                    "Redirect volunteer stewards to concessions queue management.",
                    "Broadcast halftime public announcements."
                ],
                "resource_distribution": {
                    "volunteers": "Concession Stands & Corridors",
                    "security": "VIP areas & elevators",
                    "medical": "Standby medics at concourse lobbies"
                },
                "expected_flow": "Very high density in food and washroom corridors."
            }
        elif mode == "Full Time":
            return {
                "ai_priority": "Egress Corridor Management & Transit Shuttle Desynchronization",
                "recommended_actions": [
                    "Open all exit gates to full width.",
                    "Increase Metro Shuttle headway loop by deploying 3 standby buses.",
                    "Coordinate train station entrance flows."
                ],
                "resource_distribution": {
                    "volunteers": "Exit corridors & transit station hub",
                    "security": "Gate perimeters & bus lanes",
                    "medical": "First aid rooms 3 & 4"
                },
                "expected_flow": "Egress flow peak. Maximum exit rate."
            }
        elif mode == "Emergency Mode":
            return {
                "ai_priority": "Incident Isolation & Medical Coordination",
                "recommended_actions": [
                    "Lock down affected security zones.",
                    "Deploy First Aid Squads to incident locations.",
                    "Redirect volunteer stewards to guide crowd around incident zones."
                ],
                "resource_distribution": {
                    "volunteers": "Safety corridors",
                    "security": "Lockdown boundaries",
                    "medical": "Incident zone dispatch"
                },
                "expected_flow": "Static holding pattern, localized redirect."
            }
        else: # Evacuation Mode
            return {
                "ai_priority": "Full Stadium Evacuation Plan SOP-Emergency",
                "recommended_actions": [
                    "Open all gates (Gate A to E) to 100% capacity override.",
                    "Broadcast Evacuation announcement in all 5 languages.",
                    "Deploy all staff to safety path guide duties."
                ],
                "resource_distribution": {
                    "volunteers": "Ramps, stairwells & safety exits",
                    "security": "Gate exits & perimeter clearance",
                    "medical": "Exits & standby ambulances"
                },
                "expected_flow": "Rapid exit evacuation flow. All exits prioritized."
            }
