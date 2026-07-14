import pytest
import os
from httpx import AsyncClient, ASGITransport

# Set environment keys for testing configurations
test_db_url = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ["DATABASE_URL"] = test_db_url
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "localhost:9092"
os.environ["JWT_SECRET"] = "test-secret-must-be-32-chars-long-or-more"

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select as sa_select
from backend.app.models.auth import Base, Role
from backend.app.main import app
from backend.app.core.dependencies import get_db_session
from backend.app.ai.ai_orchestrator import AIOrchestrator

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

@pytest.mark.asyncio
async def test_copilot_orchestration_structure():
    """Verify that Copilot queries return the structured 7-section layout."""
    orchestrator = AIOrchestrator()
    result = await orchestrator.execute_task(
        task_name="copilot",
        user_id="1",
        operator_role="Operator",
        inputs={"query": "Why is Gate D crowded?"}
    )
    assert "response" in result
    response_text = result["response"]
    assert "### Summary" in response_text
    assert "### Reasoning" in response_text
    assert "### Confidence" in response_text
    assert "### Recommended Actions" in response_text

@pytest.mark.asyncio
async def test_copilot_endpoint_mock_mode():
    """Verify that the POST /api/v1/ai/copilot endpoint responds correctly."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register and login user to get a valid token
        reg = await ac.post("/api/v1/auth/register", json={"email": "copilot_test@aegis.com", "password": "securepassword"})
        assert reg.status_code in (201, 400)
        
        login = await ac.post("/api/v1/auth/login", json={"email": "copilot_test@aegis.com", "password": "securepassword"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await ac.post(
            "/api/v1/ai/copilot",
            json={"query": "Show volunteer shortages"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "suggested_commands" in data
        assert "### Summary" in data["answer"]
