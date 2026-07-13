import pytest
import os
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
from backend.app.services.dashboard_service import DashboardService

test_db_url = "sqlite+aiosqlite:///./test_dashboard_timeline.db"

@pytest.fixture(autouse=True)
async def setup_db():
    os.environ["DATABASE_URL"] = test_db_url
    engine = create_async_engine(test_db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        user = User(id=1, email="op@stadium.org", hashed_password="pw", is_deleted=False)
        session.add(user)
        await session.commit()

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if os.path.exists("./test_dashboard_timeline.db"):
        try:
            os.remove("./test_dashboard_timeline.db")
        except Exception:
            pass

@pytest.mark.asyncio
async def test_timeline_event_aggregation(setup_db):
    async_session = setup_db
    async with async_session() as session:
        service = DashboardService(session)
        await service.timeline.add_event("Incident", "INCIDENT_CREATED", {"title": "Fire"})
        await service.timeline.add_event("Transit", "TRANSIT_DELAY", {"minutes": 10})

        timeline = await service.timeline.get_timeline(limit=10)
        assert len(timeline) == 2
        sources = [e["source_service"] for e in timeline]
        assert "Transit" in sources
        assert "Incident" in sources
