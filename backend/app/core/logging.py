import logging
import re
import time
from fastapi import Request
from shared.logging.logger import setup_json_logging

logger = setup_json_logging()


def _sanitize_for_logging(value: str, max_len: int = 128) -> str:
    """Prevent log injection by removing control characters and truncating."""
    if value is None:
        return "unknown"
    safe = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value))
    return safe[:max_len]


async def json_logging_middleware(request: Request, call_next):
    start_time = time.time()

    correlation_id = _sanitize_for_logging(request.headers.get("X-Correlation-ID", "unknown"))
    safe_path = _sanitize_for_logging(request.url.path)

    logger.info(
        f"Incoming request {request.method} {safe_path} (Correlation ID: {correlation_id})"
    )

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        f"Completed request {request.method} {safe_path} with status {response.status_code} in {duration:.4f}s"
    )

    return response
