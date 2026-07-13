import pytest
import os

# Set environment keys for testing configurations
test_db_url = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ["DATABASE_URL"] = test_db_url
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "localhost:9092"
os.environ["JWT_SECRET"] = "test-secret-must-be-32-chars-long-or-more"

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select as sa_select
from backend.app.main import app
from backend.app.core.dependencies import get_db_session
from backend.app.models.auth import Base, Role
from backend.app.models.user_domain import UserProfile, UserPreferences, Organization, Department, Team

# Setup Async Database engine for integration testing
test_engine = create_async_engine(test_db_url, echo=False)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with test_session() as session:
        existing = (await session.execute(sa_select(Role).where(Role.name == "Steward"))).scalar_one_or_none()
        if not existing:
            role = Role(name="Steward", description="Steward staff")
            session.add(role)
            await session.commit()
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def override_get_db_session():
    async with test_session() as session:
        yield session

app.dependency_overrides[get_db_session] = override_get_db_session

@pytest.mark.asyncio
async def test_auth_registration_and_login_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register User
        reg_response = await ac.post(
            "/api/v1/auth/register",
            json={"email": "steward@aegis.com", "password": "securepassword"}
        )
        assert reg_response.status_code == 201
        
        # 2. Login User
        login_response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "steward@aegis.com", "password": "securepassword"}
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

@pytest.mark.asyncio
async def test_rbac_guard_blocks_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Attempt accessing protected route without token
        response = await ac.get("/api/v1/auth/stewards-only")
        assert response.status_code in (401, 403)
