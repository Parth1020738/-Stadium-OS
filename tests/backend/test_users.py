import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.models.auth import Base, Role
from backend.app.models.user_domain import UserProfile, UserPreferences, Organization, Department, Team
from tests.backend.test_auth import test_session, test_engine

@pytest.fixture(scope="module", autouse=True)
async def setup_users_tables():
    import backend.app.models.user_domain
    import backend.app.models.auth
    print("Base.metadata.tables.keys():", list(Base.metadata.tables.keys()))
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Register dependency override for users test module
    from backend.app.core.dependencies import get_db_session
    from tests.backend.test_auth import override_get_db_session
    app.dependency_overrides[get_db_session] = override_get_db_session
    yield
    app.dependency_overrides.pop(get_db_session, None)

@pytest.mark.asyncio
async def test_create_get_and_update_user_lifecycle():
    # 1. Create a commander access token for role operations
    access_token = create_access_token("commander-123", ["Commander"])
    headers = {"Authorization": f"Bearer {access_token}"}

    # Verify Steward and Commander role definitions exist
    async with test_session() as session:
        from sqlalchemy.future import select
        for r_name in ["Commander"]:
            stmt = select(Role).where(Role.name == r_name)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                role = Role(name=r_name)
                session.add(role)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create user
        payload = {
            "email": "testuser@aegis.com",
            "password": "strongpassword",
            "first_name": "John",
            "last_name": "Doe"
        }
        res_create = await ac.post("/api/v1/users/", json=payload)
        assert res_create.status_code == 201
        user_data = res_create.json()
        user_id = user_data["id"]

        # Get User details
        res_get = await ac.get(f"/api/v1/users/{user_id}", headers=headers)
        assert res_get.status_code == 200
        assert res_get.json()["profile"]["first_name"] == "John"

        # Update User details
        update_payload = {
            "first_name": "Johnny",
            "last_name": "Doe",
            "phone": "555-1234",
            "version_id": 1
        }
        res_update = await ac.put(f"/api/v1/users/{user_id}", json=update_payload, headers=headers)
        assert res_update.status_code == 200
        assert res_update.json()["version_id"] == 2

        # Concurrency Lock Exception test
        res_conflict = await ac.put(f"/api/v1/users/{user_id}", json=update_payload, headers=headers)
        assert res_conflict.status_code == 409

        # Delete User (Soft Delete)
        res_delete = await ac.delete(f"/api/v1/users/{user_id}", headers=headers)
        assert res_delete.status_code == 204

        # Verify soft deleted user is not fetchable
        res_gone = await ac.get(f"/api/v1/users/{user_id}", headers=headers)
        assert res_gone.status_code == 404

@pytest.mark.asyncio
async def test_concurrent_updates_optimistic_locking():
    from sqlalchemy.future import select
    from sqlalchemy.orm.exc import StaleDataError
    from backend.app.models.auth import User

    # 1. Create a user
    async with test_session() as session1:
        user = User(email="concurrent@aegis.com", hashed_password="hashedpassword", is_deleted=False, version_id=1)
        session1.add(user)
        await session1.commit()
        user_id = user.id

    # 2. Open two separate sessions
    async with test_session() as session1, test_session() as session2:
        # Load user in session 1
        stmt1 = select(User).where(User.id == user_id)
        res1 = await session1.execute(stmt1)
        user1 = res1.scalar_one()

        # Load user in session 2
        stmt2 = select(User).where(User.id == user_id)
        res2 = await session2.execute(stmt2)
        user2 = res2.scalar_one()

        # Modify user in session 1
        user1.status = "Active"
        
        # Modify user in session 2
        user2.status = "Deactivated"

        # Commit session 1 (this succeeds and increments version_id to 2)
        await session1.commit()

        # Commit session 2 (this should fail with StaleDataError because version_id in DB is now 2)
        with pytest.raises(StaleDataError):
            await session2.commit()
