class CostTracker:
    def __init__(self):
        # Pricing per 1k tokens (Gemini 2.5/1.5 Flash pricing heuristic)
        self.input_price_per_1k = 0.000075
        self.output_price_per_1k = 0.0003

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate the estimated USD cost of an AI generation."""
        in_cost = (input_tokens / 1000.0) * self.input_price_per_1k
        out_cost = (output_tokens / 1000.0) * self.output_price_per_1k
        return in_cost + out_cost
