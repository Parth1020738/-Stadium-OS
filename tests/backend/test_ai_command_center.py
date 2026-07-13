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

from backend.app.models.ai import AIRecommendation
from backend.app.services.ai_decision_service import AIDecisionService

test_db_url = "sqlite+aiosqlite:///./test_ai_cmd.db"

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
    if os.path.exists("./test_ai_cmd.db"):
        try:
            os.remove("./test_ai_cmd.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_dependencies(monkeypatch):
    from unittest.mock import AsyncMock
    class MockProducer:
        async def send_event(self, topic, key, value): return True
    monkeypatch.setattr("backend.app.services.ai_decision_service.kafka_producer", MockProducer())
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    monkeypatch.setattr("backend.app.core.redis.redis_manager.client", mock_redis)

@pytest.mark.asyncio
async def test_accepted_recommendation_links_to_command_center(setup_db):
    async_session = setup_db
    async with async_session() as session:
        # Create recommendation with suggested command payload
        rec = AIRecommendation(
            recommendation_type="Transit",
            recommendation="Open emergency lane",
            confidence=0.95,
            priority="High",
            reason="Bus congestion",
            status="Proposed",
            suggested_commands=[{"command_type": "TRANSIT_ROUTE_OVERRIDE", "payload": {"route": "A"}}]
        )
        session.add(rec)
        user = User(id=1, email="op@stadium.org", hashed_password="pw", is_deleted=False)
        session.add(user)
        await session.commit()

        service = AIDecisionService(session)
        accepted_rec = await service.accept_recommendation(rec.id, user_id=1)
        assert accepted_rec is not None
        assert accepted_rec.status == "Accepted"

        # Verify command execution was created in database
        from backend.app.models.command import Command
        from sqlalchemy.future import select
        stmt = select(Command)
        res = await session.execute(stmt)
        cmds = res.scalars().all()
        assert len(cmds) > 0
        assert cmds[0].command_type == "TRANSIT_ROUTE_OVERRIDE"
        assert cmds[0].created_by_id == 1
