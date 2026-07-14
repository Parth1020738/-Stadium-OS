import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from backend.app.models.ai import AIAudit

logger = logging.getLogger("ai_audit")

class AuditService:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def log_request(
        self,
        operator_id: Optional[int],
        action: str,
        prompt: str,
        response: str,
        latency_ms: float,
        model: str,
        tokens_used: int,
        estimated_cost: float,
        status: str,
        context_hash: Optional[str] = None
    ):
        """Audit the AI request to database and system logs."""
        details = {
            "prompt_preview": prompt[:150],
            "response_preview": response[:150],
            "latency_ms": latency_ms,
            "model": model,
            "tokens_used": tokens_used,
            "estimated_cost_usd": estimated_cost,
            "status": status,
            "context_hash": context_hash,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Log via stdout / standard logging
        logger.info(f"AI Audit [{action}]: actor_id={operator_id}, status={status}, latency={latency_ms}ms, cost=${estimated_cost:.6f}")

        # Persist to database if session is present
        if self.db:
            try:
                audit_log = AIAudit(
                    actor_id=operator_id,
                    action=action,
                    details=details
                )
                self.db.add(audit_log)
                await self.db.commit()
            except Exception as e:
                logger.error(f"Failed to persist AI audit record: {str(e)}")
