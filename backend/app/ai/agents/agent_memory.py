import time
from typing import Dict, Any, List, Optional

class AgentMemory:
    """In-memory store for Multi-Agent context & memory lookup."""
    def __init__(self):
        self.past_decisions: List[Dict[str, Any]] = []
        self.past_simulations: List[Dict[str, Any]] = []
        self.operator_preferences: Dict[str, Any] = {
            "safety_priority": "High",
            "sustainability_weight": "Medium",
            "transit_coordination": "Auto"
        }
        self.active_commands: List[Dict[str, Any]] = []

    def record_decision(self, query: str, plan: Dict[str, Any]):
        self.past_decisions.append({
            "timestamp": time.time(),
            "query": query,
            "plan": plan
        })
        if len(self.past_decisions) > 50:
            self.past_decisions.pop(0)

    def record_simulation(self, scenario_name: str, results: Dict[str, Any]):
        self.past_simulations.append({
            "timestamp": time.time(),
            "scenario": scenario_name,
            "results": results
        })

    def get_context_summary(self) -> str:
        """Returns a string summarizing recent actions & preferences for LLM prompt context."""
        summary_lines = []
        if self.past_decisions:
            recent = self.past_decisions[-2:]
            summary_lines.append("Recent Operator Queries & Plans:")
            for item in recent:
                summary_lines.append(f"- Query: '{item['query']}'")
        if self.past_simulations:
            summary_lines.append(f"Simulations run: {len(self.past_simulations)} recent scenarios.")
        summary_lines.append(f"Operator preferences: {str(self.operator_preferences)}")
        return "\n".join(summary_lines)

# Global memory instance for easy sharing across endpoints
global_agent_memory = AgentMemory()
