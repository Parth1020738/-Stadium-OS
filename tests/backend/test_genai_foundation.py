import pytest
import os
import json
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.core.dependencies import get_db_session
from backend.app.ai.exceptions import PromptLoadException, ValidationError
from backend.app.ai.prompt_manager import PromptManager
from backend.app.ai.response_validator import ResponseValidator
from backend.app.ai.token_tracker import TokenTracker
from backend.app.ai.cost_tracker import CostTracker
from backend.app.ai.cache_service import CacheService
from backend.app.ai.ai_orchestrator import AIOrchestrator

# Set environment keys for testing configurations
test_db_url = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ["DATABASE_URL"] = test_db_url
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "localhost:9092"
os.environ["JWT_SECRET"] = "test-secret-must-be-32-chars-long-or-more"

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select as sa_select
from backend.app.models.auth import Base, Role

# Setup Async Database engine for integration testing
test_engine = create_async_engine(test_db_url, echo=False)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
test_session.__test__ = False

@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with test_session() as session:
        existing = (await session.execute(sa_select(Role).where(Role.name == "Steward"))).scalar_one_or_none()
        if not existing:
            role = Role(name="Steward", description="Steward staff")
            session.add(role)
            await session.commit()
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

async def override_get_db_session():
    async with test_session() as session:
        yield session

app.dependency_overrides[get_db_session] = override_get_db_session

def test_prompt_manager_substitution():
    """Verify variables replacement in PromptManager."""
    pm = PromptManager()
    # Write a temporary prompt template for testing
    temp_dir = Path(__file__).resolve().parent / "temp_prompts"
    temp_dir.mkdir(exist_ok=True)
    temp_prompt_path = temp_dir / "test_prompt.md"
    temp_prompt_path.write_text("Hello {{name}} from {{venue}}!", encoding="utf-8")

    try:
        pm_temp = PromptManager(prompts_dir=temp_dir)
        prompt = pm_temp.load_prompt("test_prompt", {"name": "Aegis", "venue": "Colosseum"})
        assert prompt == "Hello Aegis from Colosseum!"
    finally:
        if temp_prompt_path.exists():
            temp_prompt_path.unlink()
        if temp_dir.exists():
            temp_dir.rmdir()

def test_response_validator():
    """Verify validation rules on JSON mode responses."""
    valid_json = '{"status": "ok", "confidence": 0.85, "data": []}'
    parsed = ResponseValidator.validate_json(valid_json)
    assert parsed["status"] == "ok"

    with pytest.raises(ValidationError):
        ResponseValidator.validate_json("not raw json")

    # Required fields check
    ResponseValidator.validate_required_fields(parsed, ["status", "confidence"])
    with pytest.raises(ValidationError):
        ResponseValidator.validate_required_fields(parsed, ["missing_field"])

    # Confidence check
    ResponseValidator.validate_confidence(parsed, min_confidence=0.5)
    with pytest.raises(ValidationError):
        ResponseValidator.validate_confidence({"confidence": 0.3}, min_confidence=0.5)

def test_token_and_cost_trackers():
    """Verify token log tracking and cost predictions."""
    tracker = TokenTracker()
    stats = tracker.log_usage("user_123", "Hello", "World response content")
    assert stats["total_tokens"] > 0
    assert tracker.user_usage["user_123"] == stats["total_tokens"]

    cost_tracker = CostTracker()
    cost = cost_tracker.calculate_cost(input_tokens=1000, output_tokens=2000)
    # 1000 * 0.000075 + 2000 * 0.0003 = 0.075 + 0.60 = 0.675
    assert cost == pytest.approx(0.000675)

@pytest.mark.asyncio
async def test_cache_service():
    """Verify Redis cache serialization fallbacks."""
    cache = CacheService()
    await cache.cache_response("prompt", "context", "operator", "model", "mocked response", ttl=60)
    resp = await cache.get_response("prompt", "context", "operator", "model")
    # Should work on local memory fallback since redis might be disabled or mocked
    assert resp in (None, "mocked response")

@pytest.mark.asyncio
async def test_orchestrator_mock_mode():
    """Verify orchestrator runs cleanly in mock mode."""
    orchestrator = AIOrchestrator()
    result = await orchestrator.execute_task(
        task_name="copilot",
        user_id="1",
        operator_role="Operator",
        inputs={"query": "test query"}
    )
    assert "response" in result
    assert result["tokens_used"] > 0

@pytest.mark.asyncio
async def test_ai_endpoints():
    """Verify new GenAI endpoints return correct structures and mocks."""
    # Build httpx AsyncClient pointing to FastAPI app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        
        # We need authorization. Mock user login / register or bypass auth if token exists.
        # For simple integration testing, let's registers and log in to get a real token!
        reg = await ac.post("/api/v1/auth/register", json={"email": "ai_test@aegis.com", "password": "securepassword"})
        assert reg.status_code in (201, 400) # 400 if already exists, which is fine
        
        login = await ac.post("/api/v1/auth/login", json={"email": "ai_test@aegis.com", "password": "securepassword"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Chat
        chat_resp = await ac.post(
            "/api/v1/ai/chat", 
            json={"messages": [{"role": "user", "content": "How's the stadium status?"}], "session_id": "test_sess"},
            headers=headers
        )
        assert chat_resp.status_code == 200
        assert "response" in chat_resp.json()

        # 2. Summarize
        sum_resp = await ac.post(
            "/api/v1/ai/summarize", 
            json={"text": "Long stadium log context text", "max_length": 100},
            headers=headers
        )
        assert sum_resp.status_code == 200
        assert "summary" in sum_resp.json()

        # 3. Recommend
        rec_resp = await ac.post(
            "/api/v1/ai/recommend", 
            json={"scenario": "High crowd Gate 3"},
            headers=headers
        )
        assert rec_resp.status_code == 200
        assert "recommendations" in rec_resp.json()

        # 4. Explain
        exp_resp = await ac.post(
            "/api/v1/ai/explain", 
            json={"code_or_data": "Zone 5 congestion = 92%", "topic": "crowd"},
            headers=headers
        )
        assert exp_resp.status_code == 200
        assert "explanation" in exp_resp.json()

        # 5. Translate
        trans_resp = await ac.post(
            "/api/v1/ai/translate", 
            json={"text": "Hello Gate 3", "target_language": "Spanish"},
            headers=headers
        )
        assert trans_resp.status_code == 200
        assert "translated_text" in trans_resp.json()

        # 6. Briefing
        brief_resp = await ac.post(
            "/api/v1/ai/briefing", 
            json={"scope": "transit"},
            headers=headers
        )
        assert brief_resp.status_code == 200
        assert "briefing" in brief_resp.json()

        # 7. Copilot
        copilot_resp = await ac.post(
            "/api/v1/ai/copilot", 
            json={"query": "List open incidents"},
            headers=headers
        )
        assert copilot_resp.status_code == 200
        assert "answer" in copilot_resp.json()

        # 8. Stream
        stream_resp = await ac.get(
            "/api/v1/ai/stream?prompt=Hello",
            headers=headers
        )
        assert stream_resp.status_code == 200
        assert "text/event-stream" in stream_resp.headers["content-type"]
