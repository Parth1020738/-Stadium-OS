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

test_db_url = "sqlite+aiosqlite:///./test_dashboard_notif.db"

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
    if os.path.exists("./test_dashboard_notif.db"):
        try:
            os.remove("./test_dashboard_notif.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_kafka(monkeypatch):
    class MockProducer:
        async def send_event(self, topic, key, value): return True
    monkeypatch.setattr("backend.app.services.dashboard_service.kafka_producer", MockProducer())

@pytest.mark.asyncio
async def test_notification_creation_and_dismissal(setup_db):
    async_session = setup_db
    async with async_session() as session:
        service = DashboardService(session)
        notif = await service.notifications.create_notification("Critical", "Power failure in sector B")
        assert notif.id is not None
        assert notif.is_dismissed is False

        dismissed = await service.notifications.dismiss_notification(notif.id, 1)
        assert dismissed is not None
        assert dismissed.is_dismissed is True
        assert dismissed.dismissed_by_id == 1
