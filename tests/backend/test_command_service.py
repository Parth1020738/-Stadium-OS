import pytest
import os
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.models.auth import Base, User
from backend.app.models.command import Command
from backend.app.services.command_service import CommandGatewayService

test_db_url = "sqlite+aiosqlite:///./test_command_service.db"

@pytest.fixture(autouse=True)
async def setup_db():
    os.environ["DATABASE_URL"] = test_db_url
    engine = create_async_engine(test_db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed mock user
    async with async_session() as session:
        user = User(id=1, email="op1@stadium.org", hashed_password="pw", is_deleted=False)
        session.add(user)
        await session.commit()

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if os.path.exists("./test_command_service.db"):
        try:
            os.remove("./test_command_service.db")
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
async def test_submit_command_non_critical(setup_db):
    async_session = setup_db
    async with async_session() as session:
        service = CommandGatewayService(session)
        
        # Non-critical command executes directly
        command = await service.submit_command(
            command_type="Create Incident",
            payload={
                "title": "Unruly fan",
                "description": "Throwing water bottles",
                "severity": "Medium",
                "priority": "Medium",
                "category": "Security",
                "location_zone": "Zone A",
                "location_details": "Block 102",
                "sla_minutes": 15
            },
            creator_id=1
        )
        
        assert command.status == "Executed"
        assert command.created_by_id == 1
