import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
import pytest
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
import backend.app.models.ai

from backend.app.core.security import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

test_db_url = "sqlite+aiosqlite:///./test_ai_api.db"

@pytest.fixture(scope="module", autouse=True)
async def setup_db():
    old_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_db_url
    engine = create_async_engine(test_db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    from backend.app.core.dependencies import get_db_session
    async def override_get_db_session():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    app.dependency_overrides[get_db_session] = override_get_db_session

    # Seed User
    async with async_session() as session:
        user = User(id=1, email="operator@aegis.com", hashed_password="pw", is_deleted=False)
        session.add(user)
        await session.commit()

    yield
    
    app.dependency_overrides.pop(get_db_session, None)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if old_db_url is not None:
        os.environ["DATABASE_URL"] = old_db_url
    else:
        os.environ.pop("DATABASE_URL", None)
    if os.path.exists("./test_ai_api.db"):
        try:
            os.remove("./test_ai_api.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_dependencies(monkeypatch):
    from unittest.mock import AsyncMock
    # Kafka
    class MockProducer:
        async def send_event(self, topic, key, value): return True
    monkeypatch.setattr("backend.app.services.ai_decision_service.kafka_producer", MockProducer())
    # Redis
    mock_redis = AsyncMock()
    async def mock_get(key):
        if "density" in key:
            return b"0.92"
        if "incidents_count" in key:
            return b"5"
        return None
    mock_redis.get.side_effect = mock_get
    monkeypatch.setattr("backend.app.core.redis.redis_manager.client", mock_redis)

@pytest.fixture
def auth_header():
    token_payload = {
        "sub": "operator@aegis.com",
        "user_id": 1,
        "roles": ["Operator"],
        "jti": "some-random-uuid-string-1",
        "exp": datetime.now(timezone.utc).timestamp() + 3600
    }
    token = jwt.encode(token_payload, settings.JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_ai_rest_endpoints(auth_header):
    pass

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # GET overview
        res = await client.get("/api/v1/ai/overview", headers=auth_header)
        assert res.status_code == 200
        
        # GET risk
        res = await client.get("/api/v1/ai/risk", headers=auth_header)
        assert res.status_code == 200

        # GET recommendations
        res = await client.get("/api/v1/ai/recommendations", headers=auth_header)
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0
        rec_id = data[0]["id"]

        # POST accept
        res = await client.post(f"/api/v1/ai/recommendations/{rec_id}/accept", headers=auth_header)
        assert res.status_code == 200
        assert res.json()["status"] == "Accepted"

        # GET matchday mode
        res = await client.get("/api/v1/ai/matchday/mode", headers=auth_header)
        assert res.status_code == 200
        assert "mode" in res.json()

        # POST matchday mode
        res = await client.post("/api/v1/ai/matchday/mode?mode=Halftime", headers=auth_header)
        assert res.status_code == 200
        assert res.json()["mode"] == "Halftime"

        # POST demo trigger
        res = await client.post("/api/v1/ai/demo/trigger?scenario=crowd_surge", headers=auth_header)
        assert res.status_code == 200
        assert res.json()["scenario"] == "crowd_surge"

        # POST copilot detailed
        res = await client.post("/api/v1/ai/copilot", json={"query": "Why is Gate A congested?"}, headers=auth_header)
        assert res.status_code == 200
        assert "summary" in res.json()
        assert "risk" in res.json()

