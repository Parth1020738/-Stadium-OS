import time
import hashlib
from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

# Import modules from our infrastructure
from backend.app.ai.exceptions import AIServiceException, ValidationError
from backend.app.ai.gemini_service import GeminiService
from backend.app.ai.prompt_manager import PromptManager
from backend.app.ai.context_builder import ContextBuilder
from backend.app.ai.conversation_memory import ConversationMemory
from backend.app.ai.cache_service import CacheService
from backend.app.ai.response_validator import ResponseValidator
from backend.app.ai.token_tracker import TokenTracker
from backend.app.ai.cost_tracker import CostTracker
from backend.app.ai.audit_service import AuditService

class AIOrchestrator:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.gemini = GeminiService()
        self.prompt_manager = PromptManager()
        self.context_builder = ContextBuilder(db)
        self.memory = ConversationMemory()
        self.cache = CacheService()
        self.token_tracker = TokenTracker()
        self.cost_tracker = CostTracker()
        self.audit = AuditService(db)

    async def execute_task(
        self,
        task_name: str,
        user_id: str,
        operator_role: str,
        inputs: Dict[str, Any],
        session_id: Optional[str] = None,
        json_mode: bool = False,
        required_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Orchestrate the end-to-end AI completion execution."""
        start_time = time.time()
        
        # 1. Build real-time context
        context = await self.context_builder.build_context(operator_role, session_id)
        
        # Combine template variables
        variables = {**context, **inputs}
        
        # 2. Load prompt template
        try:
            prompt = self.prompt_manager.load_prompt(task_name, variables)
        except Exception:
            # Fallback direct prompt if loading fails
            prompt = str(inputs.get("query", inputs.get("text", "Default task request")))

        system_prompt = self.prompt_manager.load_prompt("system", variables)

        # 3. Check Redis cache
        context_str = str(sorted(context.items()))
        if not self.gemini.enable_mock:
            cached = await self.cache.get_response(prompt, context_str, user_id, self.gemini.model)
            if cached:
                latency = (time.time() - start_time) * 1000
                await self.audit.log_request(
                    operator_id=int(user_id) if user_id.isdigit() else None,
                    action=f"CACHE_HIT_{task_name.upper()}",
                    prompt=prompt,
                    response=cached,
                    latency_ms=latency,
                    model=self.gemini.model,
                    tokens_used=0,
                    estimated_cost=0.0,
                    status="SUCCESS",
                    context_hash=hashlib.sha256(context_str.encode()).hexdigest()
                )
                if json_mode:
                    try:
                        return ResponseValidator.validate_json(cached)
                    except ValidationError:
                        pass
                return {"response": cached, "cached": True}

        # 4. Generate content
        response_text = ""
        status = "SUCCESS"
        try:
            response_text = await self.gemini.generate_content(prompt, system_prompt, json_mode)
            
            # 5. Validate output
            if json_mode:
                parsed = ResponseValidator.validate_json(response_text)
                if required_fields:
                    ResponseValidator.validate_required_fields(parsed, required_fields)
                if "confidence" in parsed:
                    ResponseValidator.validate_confidence(parsed)
        except AIServiceException as e:
            status = "FAILED"
            raise e
        except Exception as e:
            status = "FAILED"
            raise AIServiceException(f"Task execution failed: {str(e)}")

        latency = (time.time() - start_time) * 1000

        # 6. Track tokens and compute cost
        token_stats = self.token_tracker.log_usage(user_id, prompt + system_prompt, response_text)
        cost = self.cost_tracker.calculate_cost(token_stats["input_tokens"], token_stats["output_tokens"])

        # 7. Audit log
        await self.audit.log_request(
            operator_id=int(user_id) if user_id.isdigit() else None,
            action=task_name.upper(),
            prompt=prompt,
            response=response_text,
            latency_ms=latency,
            model=self.gemini.model,
            tokens_used=token_stats["total_tokens"],
            estimated_cost=cost,
            status=status,
            context_hash=hashlib.sha256(context_str.encode()).hexdigest()
        )

        # 8. Cache response if successful
        if status == "SUCCESS" and not self.gemini.enable_mock:
            await self.cache.cache_response(prompt, context_str, user_id, self.gemini.model, response_text)

        if json_mode:
            return ResponseValidator.validate_json(response_text)
        return {
            "response": response_text,
            "tokens_used": token_stats["total_tokens"],
            "estimated_cost_usd": cost,
            "cached": False
        }

    async def execute_stream(
        self,
        task_name: str,
        inputs: Dict[str, Any],
        system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chunks from the Gemini API service."""
        # Simple inline format mapping
        prompt_text = str(inputs.get("query", inputs.get("text", "Default task request")))
        async for chunk in self.gemini.generate_stream(prompt_text, system_instruction):
            yield chunk
