import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
import pytest
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

test_db_url = "sqlite+aiosqlite:///./test_ai_sec.db"

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
        user = User(id=99, email="unknown@aegis.com", hashed_password="pw", is_deleted=False)
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
    if os.path.exists("./test_ai_sec.db"):
        try:
            os.remove("./test_ai_sec.db")
        except Exception:
            pass

@pytest.fixture
def auth_header_no_role():
    token_payload = {
        "sub": "unknown@aegis.com",
        "user_id": 99,
        "roles": [], # empty roles list
        "jti": "some-random-uuid-string-2",
        "exp": datetime.now(timezone.utc).timestamp() + 3600
    }
    token = jwt.encode(token_payload, settings.JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_ai_unauthorized_scope_role(auth_header_no_role):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # GET overview without required Operator/Administrator/Steward role
        res = await client.get("/api/v1/ai/overview", headers=auth_header_no_role)
        assert res.status_code == 403 # Forbidden
