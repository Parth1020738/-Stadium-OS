import pytest
import os
import uuid
import jwt
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.models.auth import Base, User
from backend.app.core.security import settings

test_db_url = "sqlite+aiosqlite:///./test_command_api.db"

@pytest.fixture(scope="module", autouse=True)
async def setup_api_db():
    os.environ["DATABASE_URL"] = test_db_url
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from backend.app.core.dependencies import get_db_session
    
    api_test_engine = create_async_engine(test_db_url, echo=False)
    api_test_session = async_sessionmaker(api_test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with api_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSession(api_test_engine) as session:
        # Seed users
        user_operator = User(id=10, email="op@stadium.org", hashed_password="pw", is_deleted=False)
        user_approver = User(id=20, email="mgr@stadium.org", hashed_password="pw", is_deleted=False)
        session.add_all([user_operator, user_approver])
        await session.commit()

    async def override_get_db_session():
        async with api_test_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    old_override = app.dependency_overrides.get(get_db_session)
    app.dependency_overrides[get_db_session] = override_get_db_session

    yield

    if old_override is not None:
        app.dependency_overrides[get_db_session] = old_override
    else:
        app.dependency_overrides.pop(get_db_session, None)

    async with api_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if os.path.exists("./test_command_api.db"):
        try:
            os.remove("./test_command_api.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_kafka_producer(monkeypatch):
    class MockKafkaProducer:
        async def start(self): pass
        async def stop(self): pass
        async def send_event(self, topic, key, value): return True
    mock = MockKafkaProducer()
    monkeypatch.setattr("backend.app.services.command_service.kafka_producer", mock)
    monkeypatch.setattr("backend.app.main.kafka_producer", mock)

@pytest.fixture(autouse=True)
async def mock_redis(monkeypatch):
    from unittest.mock import AsyncMock
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    monkeypatch.setattr("backend.app.services.command_service.redis_manager.client", mock_client)

@pytest.mark.asyncio
async def test_command_api_lifecycle():
    secret = settings.JWT_SECRET
    alg = "HS256"

    # Generate token with Operator role
    jwt_op = jwt.encode(
        {"sub": "operator", "user_id": 10, "roles": ["Operator"], "jti": str(uuid.uuid4())},
        secret, algorithm=alg
    )
    headers_op = {"Authorization": f"Bearer {jwt_op}"}

    # Generate token with Administrator / Manager role
    jwt_mgr = jwt.encode(
        {"sub": "manager", "user_id": 20, "roles": ["Administrator"], "jti": str(uuid.uuid4())},
        secret, algorithm=alg
    )
    headers_mgr = {"Authorization": f"Bearer {jwt_mgr}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create a non-critical command (executes immediately)
        payload_non_crit = {"command_type": "Create Incident", "payload": {"title": "API test incident", "description": "Desc", "severity": "Low", "priority": "Low", "category": "Security"}}
        response = await ac.post("/api/v1/commands", json=payload_non_crit, headers=headers_op)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "Executed"
        cmd_id = data["id"]

        # 2. Get command details
        response_get = await ac.get(f"/api/v1/commands/{cmd_id}", headers=headers_op)
        assert response_get.status_code == 200
        assert response_get.json()["status"] == "Executed"

        # 3. Create a critical command (awaits approval)
        payload_crit = {"command_type": "EMERGENCY_EVACUATION", "payload": {"zone": "South Corridor"}}
        response_crit = await ac.post("/api/v1/commands", json=payload_crit, headers=headers_op)
        assert response_crit.status_code == 201
        data_crit = response_crit.json()
        assert data_crit["status"] == "Pending"
        crit_cmd_id = data_crit["id"]

        # 4. Approve the critical command (via manager)
        response_approve = await ac.post(f"/api/v1/commands/{crit_cmd_id}/approve", json={"comments": "Evacuation confirmed"}, headers=headers_mgr)
        assert response_approve.status_code == 200
        assert response_approve.json()["status"] == "Executed"
