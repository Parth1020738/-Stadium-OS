from typing import Callable, Dict, Any

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable[..., Any]] = {}

    def register_tool(self, name: str, func: Callable[..., Any]):
        self._tools[name] = func

    def get_tool(self, name: str) -> Callable[..., Any]:
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found in registry.")
        return self._tools[name]

tool_registry = ToolRegistry()
