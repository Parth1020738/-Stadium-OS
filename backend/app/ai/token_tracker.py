from typing import Dict
import time

class TokenTracker:
    def __init__(self):
        # Local stats store
        self.daily_usage: Dict[str, int] = {}
        self.user_usage: Dict[str, int] = {}

    def count_tokens(self, text: str) -> int:
        """Estimate tokens based on characters (standard heuristic: ~4 chars per token)."""
        if not text:
            return 0
        return len(text) // 4 + 1

    def log_usage(self, user_id: str, input_text: str, output_text: str) -> Dict[str, int]:
        """Record usage metrics for daily and user metrics."""
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        total_tokens = input_tokens + output_tokens

        # Record today
        today = time.strftime("%Y-%m-%d")
        self.daily_usage[today] = self.daily_usage.get(today, 0) + total_tokens
        self.user_usage[user_id] = self.user_usage.get(user_id, 0) + total_tokens

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        }
