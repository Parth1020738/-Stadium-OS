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

from backend.app.models.knowledge import KnowledgeDocument
from backend.app.services.ai_decision_service import AIDecisionService

test_db_url = "sqlite+aiosqlite:///./test_ai_rag.db"

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
    if os.path.exists("./test_ai_rag.db"):
        try:
            os.remove("./test_ai_rag.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_dependencies(monkeypatch):
    from unittest.mock import AsyncMock
    class MockProducer:
        async def send_event(self, topic, key, value): return True
    monkeypatch.setattr("backend.app.services.ai_decision_service.kafka_producer", MockProducer())
    mock_redis = AsyncMock()
    async def mock_get(key):
        if "density" in key:
            return b"0.90"
        return None
    mock_redis.get.side_effect = mock_get
    monkeypatch.setattr("backend.app.services.ai_decision_service.redis_manager.client", mock_redis)

@pytest.mark.asyncio
async def test_rag_playbook_matching(setup_db):
    async_session = setup_db
    async with async_session() as session:
        # Seed Knowledge document
        doc = KnowledgeDocument(
            id=101,
            title="South corridor Crowd Evacuation Protocol",
            content="Evacuate through Gate C immediately during severe congestion.",
            status="PUBLISHED"
        )
        session.add(doc)
        await session.commit()

        service = AIDecisionService(session)
        recs = await service.generate_recommendations()
        assert len(recs) > 0
        
        # Verify references were created mapping back to Knowledge base
        rec = recs[0]
        # Query references
        from backend.app.models.ai import AIKnowledgeReference
        from sqlalchemy.future import select
        stmt = select(AIKnowledgeReference).where(AIKnowledgeReference.recommendation_id == rec.id)
        res = await session.execute(stmt)
        refs = res.scalars().all()
        assert len(refs) > 0
        assert refs[0].document_id == 101
