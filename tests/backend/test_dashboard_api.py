import pytest
import os
import uuid
import jwt
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
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
from backend.app.core.security import settings

test_db_url = "sqlite+aiosqlite:///./test_dashboard_api.db"

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
        session.add(user_operator)
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
    if os.path.exists("./test_dashboard_api.db"):
        try:
            os.remove("./test_dashboard_api.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_kafka_producer(monkeypatch):
    class MockKafkaProducer:
        async def start(self): pass
        async def stop(self): pass
        async def send_event(self, topic, key, value): return True
    mock = MockKafkaProducer()
    monkeypatch.setattr("backend.app.services.dashboard_service.kafka_producer", mock)
    monkeypatch.setattr("backend.app.main.kafka_producer", mock)

@pytest.fixture(autouse=True)
async def mock_redis(monkeypatch):
    from unittest.mock import AsyncMock
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    monkeypatch.setattr("backend.app.api.v1.endpoints.dashboard.redis_manager.client", mock_client)
    monkeypatch.setattr("backend.app.services.dashboard_service.redis_manager.client", mock_client)

@pytest.mark.asyncio
async def test_dashboard_api_routes():
    secret = settings.JWT_SECRET
    alg = "HS256"

    # Generate token with Operator role
    jwt_op = jwt.encode(
        {"sub": "operator", "user_id": 10, "roles": ["Operator"], "jti": str(uuid.uuid4())},
        secret, algorithm=alg
    )
    headers = {"Authorization": f"Bearer {jwt_op}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Overview endpoint
        response = await ac.get("/api/v1/dashboard/overview", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data

        # Metrics endpoint
        res_m = await ac.get("/api/v1/dashboard/metrics", headers=headers)
        assert res_m.status_code == 200

        # Health endpoint
        res_h = await ac.get("/api/v1/dashboard/health", headers=headers)
        assert res_h.status_code == 200
