import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select as sa_select

from backend.app.models.auth import Base, Role
from backend.app.main import app
from backend.app.core.dependencies import get_db_session
from backend.app.ai.gemini_service import GeminiService
from backend.app.ai.ai_orchestrator import AIOrchestrator

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
async def test_multilingual_translation_detection():
    """Verify that targeting Spanish or French translates the mock responses."""
    service = GeminiService()
    
    # Test Spanish translation
    es_response = service._get_mock_response("Show crowd density at Gate D in Spanish")
    assert "### Summary (ES)" in es_response
    assert "La puerta D está experimentando actualmente un aumento del 42%" in es_response

    # Test French translation
    fr_response = service._get_mock_response("Summarize incidents in French")
    assert "### Summary (FR)" in fr_response
    assert "Il y a actuellement 3 incidents actifs" in fr_response

@pytest.mark.asyncio
async def test_workflow_steps_generation():
    """Verify that mock output appends Step-by-step workflow commands."""
    service = GeminiService()
    response = service._get_mock_response("Why is Gate D crowded?")
    assert "### Workflow" in response
    assert "1. Open Gate D:" in response
    assert "2. Dispatch Volunteers:" in response
