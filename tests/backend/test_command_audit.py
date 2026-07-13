import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.models.auth import Base, User
from backend.app.services.command_service import CommandGatewayService

test_db_url = "sqlite+aiosqlite:///./test_command_audit.db"

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
    if os.path.exists("./test_command_audit.db"):
        try:
            os.remove("./test_command_audit.db")
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
async def test_command_audit_creation(setup_db):
    async_session = setup_db
    async with async_session() as session:
        service = CommandGatewayService(session)
        
        command = await service.submit_command(
            command_type="Mock Command",
            payload={"title": "Test Title"},
            creator_id=1
        )
        
        # Verify audits list is populated
        audits = await service.audit_repo.get_by_command_id(command.id)
        assert len(audits) >= 1
        assert any(a.action == "CREATE" for a in audits)
        assert any(a.new_state.get("command_type") == "Mock Command" for a in audits if a.new_state)
