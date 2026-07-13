import pytest
import os
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.models.auth import Base, User
from backend.app.services.command_service import CommandGatewayService

test_db_url = "sqlite+aiosqlite:///./test_command_kafka.db"

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
        user = User(id=1, email="op@stadium.org", hashed_password="pw", is_deleted=False)
        session.add(user)
        await session.commit()

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if os.path.exists("./test_command_kafka.db"):
        try:
            os.remove("./test_command_kafka.db")
        except Exception:
            pass

@pytest.mark.asyncio
async def test_kafka_event_publication(setup_db, monkeypatch):
    from unittest.mock import AsyncMock
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    monkeypatch.setattr("backend.app.services.command_service.redis_manager.client", mock_redis)

    send_mock = MagicMock()
    class MockProducer:
        async def send_event(self, topic, key, value):
            send_mock(topic, key, value)
            return True
            
    monkeypatch.setattr("backend.app.services.command_service.kafka_producer", MockProducer())
    
    async_session = setup_db
    async with async_session() as session:
        service = CommandGatewayService(session)
        
        await service.submit_command(
            command_type="Mock Command",
            payload={"title": "Panic"},
            creator_id=1
        )
        
        # Verify event creation was triggered
        from unittest.mock import ANY
        send_mock.assert_any_call("command.created", "1", ANY)
