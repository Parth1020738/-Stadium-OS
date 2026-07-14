class AIServiceException(Exception):
    """Base exception for all AI infrastructure errors."""
    pass

class GeminiAPIException(AIServiceException):
    """Raised when the Gemini API returns an error or fails."""
    pass

class RateLimitException(AIServiceException):
    """Raised when rate limits are exceeded."""
    pass

class ValidationError(AIServiceException):
    """Raised when response validation checks fail."""
    pass

class PromptLoadException(AIServiceException):
    """Raised when prompt templates cannot be loaded or resolved."""
    pass
