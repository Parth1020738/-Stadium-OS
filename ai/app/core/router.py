class ModelRouter:
    def __init__(self, default_model: str = "gemini-1.5-flash"):
        self.default_model = default_model

    def select_model(self, task_type: str) -> str:
        # Phase 1 Router interface
        if task_type == "complex_reasoning":
            return "gemini-1.5-pro"
        return self.default_model

model_router = ModelRouter()
