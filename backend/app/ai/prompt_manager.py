import os
from pathlib import Path
from typing import Optional
from backend.app.ai.exceptions import PromptLoadException

class PromptManager:
    def __init__(self, prompts_dir: Optional[Path] = None):
        if prompts_dir is None:
            # Locate relative to backend root
            self.prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
        else:
            self.prompts_dir = prompts_dir

    def load_prompt(self, name: str, variables: Optional[dict] = None) -> str:
        """Load prompt markdown file and substitute variables."""
        if not name.endswith(".md"):
            filename = f"{name}.md"
        else:
            filename = name

        filepath = self.prompts_dir / filename
        if not filepath.exists():
            raise PromptLoadException(f"Prompt template {filename} not found at {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise PromptLoadException(f"Failed to read prompt file: {str(e)}")

        if variables:
            for key, val in variables.items():
                placeholder = "{{" + str(key) + "}}"
                content = content.replace(placeholder, str(val if val is not None else ""))
        
        return content
