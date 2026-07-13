from typing import Any, Dict

class PromptRegistry:
    def __init__(self):
        self._templates = {
            "incident-triage-v1": "Analyze this incident details: {details}",
            "wayfinding-navigation-v1": "Locate accessible route in zone: {zone}"
        }

    def get_prompt_template(self, key: str) -> str:
        if key not in self._templates:
            raise ValueError(f"Prompt template '{key}' not registered.")
        return self._templates[key]

prompt_registry = PromptRegistry()
