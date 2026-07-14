import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select as sa_select

from backend.app.models.auth import Base, Role
from backend.app.main import app
from backend.app.core.dependencies import get_db_session
from backend.app.ai.gemini_service import GeminiService

test_db_url = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
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

@pytest.mark.asyncio
async def test_scenario_simulations():
    """Verify that match kickoff egress surge simulations generate correct workflows."""
    service = GeminiService()
    response = service._get_mock_response("simulate crowd surge at gate d")
    assert "Simulation scenario initiated" in response
    assert "### Workflow" in response
    assert "Open Gate D" in response

@pytest.mark.asyncio
async def test_sustainability_intelligence():
    """Verify that sustainability queries return temperature setbacks."""
    service = GeminiService()
    response = service._get_mock_response("Recommend HVAC and lighting energy setback")
    assert "Sustainability Intelligence Plan" in response
    assert "HVAC setback to 23C" in response

@pytest.mark.asyncio
async def test_pa_announcements():
    """Verify that PA announcements yield multilingual templates."""
    service = GeminiService()
    response = service._get_mock_response("Generate announcement for diversion")
    assert "Multilingual Public Announcement" in response
    assert "Spanish: Atención visitantes" in response
    assert "Arabic: انتباه أيها الضيوف" in response
