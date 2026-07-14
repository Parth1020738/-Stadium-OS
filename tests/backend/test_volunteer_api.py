import pytest
import os
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.models.auth import Base, User
from backend.app.core.security import create_access_token

test_db_url = "sqlite+aiosqlite:///" + os.path.abspath("./test_volunteer_api.db").replace("\\", "/")

@pytest.fixture(scope="module", autouse=True)
async def setup_api_db():
    # Set DATABASE_URL env var
    os.environ["DATABASE_URL"] = test_db_url
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    import backend.app.models.user_domain
    import backend.app.models.volunteer
    from backend.app.models.volunteer import Skill
    from backend.app.core.dependencies import get_db_session
    
    api_test_engine = create_async_engine(test_db_url, echo=False)
    api_test_session = async_sessionmaker(api_test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with api_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSession(api_test_engine) as session:
        skill1 = Skill(name="Spanish", description="Spanish language")
        skill2 = Skill(name="Wayfinding", description="Wayfinding support")
        session.add_all([skill1, skill2])
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
    await api_test_engine.dispose()
    if os.path.exists("./test_volunteer_api.db"):
        try:
            os.remove("./test_volunteer_api.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
async def mock_kafka_producer(monkeypatch):
    # Mock Kafka producer in main/service layers to avoid errors during test execution
    class MockKafkaProducer:
        async def start(self): pass
        async def stop(self): pass
        async def send_event(self, topic, key, value): return True
    mock = MockKafkaProducer()
    monkeypatch.setattr("backend.app.services.volunteer_service.kafka_producer", mock)
    monkeypatch.setattr("backend.app.main.kafka_producer", mock)

@pytest.mark.asyncio
async def test_volunteer_management_api_flow():
    # Setup base tokens
    staff_token = create_access_token("9999", ["Staff"])
    headers_staff = {"Authorization": f"Bearer {staff_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register User in core DB
        reg1 = await ac.post("/api/v1/auth/register", json={"email": "vol1@aegis.com", "password": "pw"})
        assert reg1.status_code == 201

        # Fetch registered user's ID
        users_resp = await ac.get("/api/v1/users/", headers=headers_staff)
        assert users_resp.status_code == 200
        users_list = users_resp.json()
        
        vol1_user_id = None
        for u in users_list:
            if u["email"] == "vol1@aegis.com":
                vol1_user_id = u["id"]
        assert vol1_user_id is not None

        # Generate volunteer token specific to their registered user ID
        volunteer_token = create_access_token(str(vol1_user_id), ["Volunteer"])
        headers_volunteer = {"Authorization": f"Bearer {volunteer_token}"}
        
        # Generate another volunteer token representing a different volunteer
        stranger_token = create_access_token("12345", ["Volunteer"])
        headers_stranger = {"Authorization": f"Bearer {stranger_token}"}

        # 2. Register Volunteer profile (Staff permission required)
        reg_vol_payload = {
            "user_id": vol1_user_id,
            "first_name": "Alice",
            "last_name": "Smith",
            "phone": "+15550001111",
            "email": "vol1@aegis.com",
            "preferred_language": "en",
            "bio": "Crowd control and translation"
        }
        res_reg = await ac.post("/api/v1/volunteers", json=reg_vol_payload, headers=headers_staff)
        assert res_reg.status_code == 201
        volunteer_id = res_reg.json()["id"]

        # Assign Spanish skill to volunteer
        res_skill1 = await ac.post(f"/api/v1/volunteers/{volunteer_id}/skills", json={"skill_id": 1, "proficiency_level": "Intermediate"}, headers=headers_staff)
        assert res_skill1.status_code == 201

        # Assign Wayfinding skill to volunteer
        res_skill2 = await ac.post(f"/api/v1/volunteers/{volunteer_id}/skills", json={"skill_id": 2, "proficiency_level": "Expert"}, headers=headers_staff)
        assert res_skill2.status_code == 201

        # Try to register volunteer as non-staff -> 403 Forbidden
        res_fail_reg = await ac.post("/api/v1/volunteers", json=reg_vol_payload, headers=headers_volunteer)
        assert res_fail_reg.status_code == 403

        # 3. Create Shift (Staff permission required)
        now = datetime.now(timezone.utc)
        shift_payload = {
            "name": "Concourse Translation Support",
            "description": "Spanish/English wayfinding",
            "start_time": (now + timedelta(hours=2)).isoformat(),
            "end_time": (now + timedelta(hours=6)).isoformat(),
            "location_zone": "Concourse B",
            "required_skills": "Spanish, Wayfinding"
        }
        res_shift = await ac.post("/api/v1/shifts", json=shift_payload, headers=headers_staff)
        assert res_shift.status_code == 201
        shift_id = res_shift.json()["id"]

        # 4. Assign volunteer to shift (Staff permission required)
        res_assign = await ac.post(f"/api/v1/shifts/{shift_id}/assign", json={"volunteer_id": volunteer_id}, headers=headers_staff)
        assert res_assign.status_code == 201
        assignment_id = res_assign.json()["id"]

        # 5. Check-In (Self/Volunteer or Staff permitted)
        # Attempt check-in by stranger (should raise 403 Forbidden)
        res_checkin_fail = await ac.post(f"/api/v1/shifts/assignments/{assignment_id}/check-in", json={"latitude": 25.7, "longitude": -80.1}, headers=headers_stranger)
        assert res_checkin_fail.status_code == 403

        # Successful check-in by volunteer
        res_checkin = await ac.post(f"/api/v1/shifts/assignments/{assignment_id}/check-in", json={"latitude": 25.7, "longitude": -80.1}, headers=headers_volunteer)
        assert res_checkin.status_code == 200
        assert res_checkin.json()["status"] in ("Present", "Tardy")

        # 6. Check-Out (Self/Volunteer or Staff permitted)
        res_checkout = await ac.post(f"/api/v1/shifts/assignments/{assignment_id}/check-out", json={"latitude": 25.7, "longitude": -80.1}, headers=headers_volunteer)
        assert res_checkout.status_code == 200

        # Verify statistics endpoint works
        res_stats = await ac.get("/api/v1/volunteers/statistics", headers=headers_staff)
        assert res_stats.status_code == 200
        assert res_stats.json()["total_volunteers"] == 1

        # 7. Add Certification (Self/Volunteer or Staff permitted)
        cert_payload = {
            "name": "First Aid Basic",
            "issuing_authority": "Red Cross",
            "license_number": "FA-98765",
            "issue_date": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "expiry_date": (datetime.now(timezone.utc) + timedelta(days=360)).isoformat()
        }
        res_cert = await ac.post(f"/api/v1/volunteers/{volunteer_id}/certifications", json=cert_payload, headers=headers_volunteer)
        assert res_cert.status_code == 201

        # Verify Certification (Staff permission required)
        res_verify = await ac.post(
            f"/api/v1/volunteers/{volunteer_id}/certifications/1/verify",
            params={"status": "Verified"},
            headers=headers_staff
        )
        assert res_verify.status_code == 200
        assert res_verify.json()["verification_status"] == "Verified"
