import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.models.auth import Base
import backend.app.models.command # Load command tables
from backend.app.models.command import Command
from backend.app.repositories.command_repository import CommandRepository

test_db_url = "sqlite+aiosqlite:///./test_command_repo.db"

@pytest.fixture(autouse=True)
async def setup_db():
    os.environ["DATABASE_URL"] = test_db_url
    engine = create_async_engine(test_db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if os.path.exists("./test_command_repo.db"):
        try:
            os.remove("./test_command_repo.db")
        except Exception:
            pass

@pytest.mark.asyncio
async def test_command_crud(setup_db):
    async_session = setup_db
    async with async_session() as session:
        repo = CommandRepository(session)
        
        command = Command(
            command_type="Create Incident",
            payload={"title": "Test Title"},
            status="Pending",
            correlation_id="corr-1"
        )
        await repo.create(command)
        await repo.commit()
        
        db_cmd = await repo.get_by_id(command.id)
        assert db_cmd is not None
        assert db_cmd.command_type == "Create Incident"
        assert db_cmd.status == "Pending"
        
        # Test List
        cmds = await repo.list_commands(limit=10)
        assert len(cmds) == 1
