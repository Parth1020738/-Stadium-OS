import pytest
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select as sa_select

test_db_url = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ["DATABASE_URL"] = test_db_url

from backend.app.models.auth import Base, Role
from backend.app.main import app
from backend.app.core.dependencies import get_db_session
from backend.app.ai.agents.multi_agent_coordinator import MultiAgentCoordinator

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
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

async def override_get_db_session():
    async with test_session() as session:
        yield session

app.dependency_overrides[get_db_session] = override_get_db_session


@pytest.mark.asyncio
async def test_coordinator_and_agents_logic():
    """Verify that MultiAgentCoordinator correctly runs agents and structures plans."""
    coordinator = MultiAgentCoordinator()
    context = {
        "current_time": "2026-07-14T12:00:00Z",
        "venue": "Aegis Colosseum",
        "weather": "Rainy, 18°C",
        "crowd": "High flow, 90% capacity",
        "incidents": "1 water leak",
        "transit": "Delayed shuttles",
        "volunteers": "40 active",
        "accessibility": "Nominal"
    }
    
    plan = await coordinator.generate_action_plan(
        query="Gate D emergency overcrowding and shuttle delay",
        context=context
    )
    
    # Check plan format
    assert "query" in plan
    assert "agents" in plan
    assert "timeline" in plan
    assert "resource_optimizations" in plan
    assert "confidence" in plan
    
    # Check agents list
    agents_res = plan["agents"]
    assert "crowd" in agents_res
    assert "transit" in agents_res
    assert "security" in agents_res
    assert "weather" in agents_res
    
    # Check structured output of crowd agent
    assert agents_res["crowd"]["name"] == "Crowd Agent"
    assert agents_res["crowd"]["confidence"] >= 0.90
    
    # Check briefings compile
    briefings = coordinator.generate_briefings(plan)
    assert "ceo" in briefings
    assert "operations" in briefings
    assert "transit" in briefings
    assert briefings["ceo"]["role_title"] == "Chief Executive Officer"

@pytest.mark.asyncio
async def test_multi_agent_endpoints():
    """Verify that POST /api/v1/ai/multi-agent/plan and GET /api/v1/ai/multi-agent/memory work."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register and login to acquire standard JWT
        reg = await ac.post("/api/v1/auth/register", json={"email": "agent_test@aegis.com", "password": "securepassword"})
        assert reg.status_code in (201, 400)
        
        login = await ac.post("/api/v1/auth/login", json={"email": "agent_test@aegis.com", "password": "securepassword"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test POST plan
        response = await ac.post(
            "/api/v1/ai/multi-agent/plan",
            json={"query": "Gate C conflict overcrowding incident"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert "briefings" in data
        
        # Verify conflict resolution details
        plan_data = data["plan"]
        assert len(plan_data["conflicts"]) > 0
        assert "resolution" in plan_data["conflicts"][0]

        # Test GET memory
        mem_resp = await ac.get("/api/v1/ai/multi-agent/memory", headers=headers)
        assert mem_resp.status_code == 200
        mem_data = mem_resp.json()
        assert "past_decisions" in mem_data
        assert "operator_preferences" in mem_data
