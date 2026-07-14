import json
from typing import List, Dict, Any, Optional
from backend.app.ai.exceptions import ValidationError

class ResponseValidator:
    @staticmethod
    def validate_json(raw_response: str) -> Dict[str, Any]:
        """Verify that response is a valid JSON string."""
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Response is not valid JSON: {str(e)}")

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]):
        """Verify required fields exist in parsed JSON."""
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValidationError(f"Missing required fields in AI response: {missing}")

    @staticmethod
    def validate_confidence(data: Dict[str, Any], min_confidence: float = 0.5):
        """Sanity check on confidence scores."""
        confidence = data.get("confidence")
        if confidence is not None:
            try:
                conf_val = float(confidence)
                if conf_val < 0.0 or conf_val > 1.0:
                    raise ValidationError(f"Confidence score {conf_val} is out of bounds [0, 1].")
                if conf_val < min_confidence:
                    raise ValidationError(f"AI response confidence ({conf_val}) is below minimum threshold ({min_confidence}).")
            except ValueError:
                raise ValidationError("Confidence score is not a valid number.")
