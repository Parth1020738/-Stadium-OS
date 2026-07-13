import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.models.auth import Base, User
from backend.app.services.command_service import CommandGatewayService

test_db_url = "sqlite+aiosqlite:///./test_command_approval.db"

@pytest.fixture(autouse=True)
async def setup_db():
    os.environ["DATABASE_URL"] = test_db_url
    engine = create_async_engine(test_db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed mock user and approver
    async with async_session() as session:
        user1 = User(id=1, email="op@stadium.org", hashed_password="pw", is_deleted=False)
        user2 = User(id=2, email="app@stadium.org", hashed_password="pw", is_deleted=False)
        session.add_all([user1, user2])
        await session.commit()

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if os.path.exists("./test_command_approval.db"):
        try:
            os.remove("./test_command_approval.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_kafka(monkeypatch):
    class MockProducer:
        async def send_event(self, topic, key, value): return True
    monkeypatch.setattr("backend.app.services.command_service.kafka_producer", MockProducer())

@pytest.fixture(autouse=True)
async def mock_redis(monkeypatch):
    from unittest.mock import AsyncMock
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    monkeypatch.setattr("backend.app.services.command_service.redis_manager.client", mock_client)

@pytest.mark.asyncio
async def test_critical_command_requires_approval(setup_db):
    async_session = setup_db
    async with async_session() as session:
        service = CommandGatewayService(session)
        
        # Critical command
        command = await service.submit_command(
            command_type="EMERGENCY_EVACUATION",
            payload={"zone": "North Exit"},
            creator_id=1
        )
        
        assert command.status == "Pending"
        
        # Approver approves command
        approved_cmd = await service.approve_command(
            command_id=command.id,
            approver_id=2,
            comments="Approved evacuation route"
        )
        
        assert approved_cmd.status == "Executed"
