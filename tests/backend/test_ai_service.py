import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.app.models.auth import Base, User
import backend.app.models.user_domain
import backend.app.models.knowledge
import backend.app.models.crowd
import backend.app.models.incident
import backend.app.models.volunteer
import backend.app.models.transit
import backend.app.models.accessibility
import backend.app.models.command
import backend.app.models.dashboard
import backend.app.models.ai

from backend.app.services.ai_decision_service import AIDecisionService

test_db_url = "sqlite+aiosqlite:///./test_ai_service.db"

@pytest.fixture(autouse=True)
async def setup_db():
    old_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_db_url
    engine = create_async_engine(test_db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield async_session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if old_db_url is not None:
        os.environ["DATABASE_URL"] = old_db_url
    else:
        os.environ.pop("DATABASE_URL", None)
    if os.path.exists("./test_ai_service.db"):
        try:
            os.remove("./test_ai_service.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_dependencies(monkeypatch):
    from unittest.mock import AsyncMock
    # Kafka
    class MockProducer:
        async def send_event(self, topic, key, value): return True
    monkeypatch.setattr("backend.app.services.ai_decision_service.kafka_producer", MockProducer())
    # Redis
    mock_redis = AsyncMock()
    async def mock_get(key):
        if "density" in key:
            return b"0.92"
        if "incidents_count" in key:
            return b"5"
        return None
    mock_redis.get.side_effect = mock_get
    monkeypatch.setattr("backend.app.services.ai_decision_service.redis_manager.client", mock_redis)

@pytest.mark.asyncio
async def test_recommendation_generation(setup_db):
    async_session = setup_db
    async with async_session() as session:
        # Create a mock user
        user = User(id=1, email="op@stadium.org", hashed_password="pw", is_deleted=False)
        session.add(user)
        await session.commit()

        service = AIDecisionService(session)
        recs = await service.generate_recommendations()
        assert len(recs) > 0
        assert recs[0].confidence > 0.8
