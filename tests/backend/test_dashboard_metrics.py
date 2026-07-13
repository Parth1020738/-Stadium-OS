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

test_db_url = "sqlite+aiosqlite:///./test_dashboard_metrics.db"

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
    if os.path.exists("./test_dashboard_metrics.db"):
        try:
            os.remove("./test_dashboard_metrics.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_kafka(monkeypatch):
    class MockProducer:
        async def send_event(self, topic, key, value): return True
    monkeypatch.setattr("backend.app.services.dashboard_service.kafka_producer", MockProducer())

@pytest.fixture(autouse=True)
async def mock_redis(monkeypatch):
    from unittest.mock import AsyncMock
    mock_client = AsyncMock()
    async def mock_get(key):
        if "density" in key:
            return b"0.65"
        if "incidents_count" in key:
            return b"5"
        return None
    mock_client.get.side_effect = mock_get
    monkeypatch.setattr("backend.app.services.dashboard_service.redis_manager.client", mock_client)

@pytest.mark.asyncio
async def test_kpi_engine_calculation(setup_db):
    async_session = setup_db
    async with async_session() as session:
        service = DashboardService(session)
        kpis = await service.metrics.get_kpis()
        assert kpis["average_density"] == 0.65
        assert kpis["current_attendance"] == 45000
        assert kpis["dashboard_health"] == "Healthy"
