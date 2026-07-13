import pytest
import os
import uuid
import jwt
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

test_db_url = "sqlite+aiosqlite:///./test_dashboard_sec.db"

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
    if os.path.exists("./test_dashboard_sec.db"):
        try:
            os.remove("./test_dashboard_sec.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_redis(monkeypatch):
    from unittest.mock import AsyncMock
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    monkeypatch.setattr("backend.app.api.v1.endpoints.dashboard.redis_manager.client", mock_client)
    monkeypatch.setattr("backend.app.services.dashboard_service.redis_manager.client", mock_client)

@pytest.mark.asyncio
async def test_dashboard_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Request without headers -> 403 Forbidden
        response = await ac.get("/api/v1/dashboard/overview")
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_dashboard_role_rejection():
    secret = settings.JWT_SECRET
    alg = "HS256"
    # Generate token with Guest role (not allowed)
    jwt_guest = jwt.encode(
        {"sub": "guest", "user_id": 99, "roles": ["Guest"], "jti": str(uuid.uuid4())},
        secret, algorithm=alg
    )
    headers = {"Authorization": f"Bearer {jwt_guest}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/dashboard/overview", headers=headers)
        assert response.status_code == 403
