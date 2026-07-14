import pytest
import os
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.models.auth import Base, User
from backend.app.models.accessibility import (
    AccessibilityFacility, 
    AccessibilityMap, 
    AccessibilityBarrier,
    AccessibilityRoute,
    AccessibilityWaypoint,
    AccessibilityAlert,
    AccessibilityAudit
)
from backend.app.core.security import settings

test_db_url = "sqlite+aiosqlite:///" + os.path.abspath("./test_accessibility_api.db").replace("\\", "/")

@pytest.fixture(scope="module", autouse=True)
async def setup_api_db():
    os.environ["DATABASE_URL"] = test_db_url
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from backend.app.core.dependencies import get_db_session
    
    api_test_engine = create_async_engine(test_db_url, echo=False)
    api_test_session = async_sessionmaker(api_test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with api_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        # Force registration of all models
        import backend.app.models.accessibility
        print("Accessibility tables:", list(Base.metadata.tables.keys()))
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSession(api_test_engine) as session:
        # Create map and facility for reference
        acc_map = AccessibilityMap(venue_id="venue_123", status="Active")
        facility = AccessibilityFacility(
            id="fac_elevator_b02",
            venue_id="venue_123",
            name="Concourse B elevator B02",
            facility_type="ELEVATOR",
            status="Active"
        )
        session.add_all([acc_map, facility])
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
    if os.path.exists("./test_accessibility_api.db"):
        try:
            os.remove("./test_accessibility_api.db")
        except Exception:
            pass


@pytest.fixture(autouse=True)
async def mock_kafka_producer(monkeypatch):
    class MockKafkaProducer:
        async def start(self): pass
        async def stop(self): pass
        async def send_event(self, topic, key, value): return True
    mock = MockKafkaProducer()
    monkeypatch.setattr("backend.app.services.accessibility_service.kafka_producer", mock)
    monkeypatch.setattr("backend.app.main.kafka_producer", mock)


@pytest.mark.asyncio
async def test_accessibility_api_rbac_and_flow():
    secret = settings.JWT_SECRET
    alg = "HS256"

    # Generate token with accessibility:read
    jwt_read = jwt.encode(
        {"sub": "1001", "roles": ["Operator"], "scopes": ["accessibility:read"], "jti": str(uuid.uuid4())},
        secret, algorithm=alg
    )
    headers_read = {"Authorization": f"Bearer {jwt_read}"}

    # Generate token with accessibility:write
    jwt_write = jwt.encode(
        {"sub": "1002", "roles": ["Operator"], "scopes": ["accessibility:write"], "jti": str(uuid.uuid4())},
        secret, algorithm=alg
    )
    headers_write = {"Authorization": f"Bearer {jwt_write}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Fetch map (requires read scope)
        res_map = await ac.get("/api/v1/venues/venue_123/accessibility/map", headers=headers_read)
        assert res_map.status_code == 200
        assert res_map.json()["venue_id"] == "venue_123"

        # 2. Register barrier (requires write scope)
        barrier_payload = {
            "traceId": "tr-dd90a82e",
            "correlationId": "corr-505aaef1",
            "clientTimestamp": "2026-07-09T11:23:00Z",
            "clientVersion": "BmsIntegrator-v1.0",
            "data": {
                "barrier_type": "ELEVATOR_OUTAGE",
                "severity": "CRITICAL",
                "zone_id": "zone_b_concourse",
                "location_label": "Concourse B elevator B02",
                "associated_facility_id": "fac_elevator_b02",
                "latitude": 25.778150,
                "longitude": -80.191350,
                "bms_fault_code": "ERR_ELEV_MOTOR_OVERHEAT"
            }
        }
        res_b = await ac.post("/api/v1/venues/venue_123/accessibility/barriers", json=barrier_payload, headers=headers_write)
        assert res_b.status_code == 201
        res_data = res_b.json()
        assert res_data["data"]["status"] == "ACTIVE_BARRIER_REGISTERED"
        barrier_id = res_data["data"]["barrier_id"]

        # 3. Create route (requires read scope)
        route_payload = {
            "start_zone_id": "zone_b_perimeter",
            "end_zone_id": "section_112_ada_tier",
            "impairment_profile": "WHEELCHAIR_ACCESSIBLE",
            "generate_audio_instructions": True,
            "audio_language": "es"
        }
        res_r = await ac.post("/api/v1/venues/venue_123/accessibility/routes", json=route_payload, headers=headers_read)
        assert res_r.status_code == 200
        route_data = res_r.json()
        assert route_data["data"]["status"] == "Active"

        # 4. Resolve barrier
        res_del = await ac.delete(f"/api/v1/venues/venue_123/accessibility/barriers/{barrier_id}", headers=headers_write)
        assert res_del.status_code == 204


@pytest.mark.asyncio
async def test_accessibility_pagination_and_timezone():
    print("Overrides in pagination test:", app.dependency_overrides)
    secret = settings.JWT_SECRET
    alg = "HS256"

    # Generate token with Admin roles
    jwt_admin = jwt.encode(
        {"sub": "1000", "roles": ["Admin"], "scopes": ["accessibility:read", "accessibility:write"], "jti": str(uuid.uuid4())},
        secret, algorithm=alg
    )
    headers = {"Authorization": f"Bearer {jwt_admin}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Verify invalid timezone-naive clientTimestamp is rejected
        barrier_payload_naive = {
            "traceId": "tr-dd90a82e",
            "correlationId": "corr-505aaef1",
            "clientTimestamp": "2026-07-09T11:23:00",
            "clientVersion": "BmsIntegrator-v1.0",
            "data": {
                "barrier_type": "ELEVATOR_OUTAGE",
                "severity": "CRITICAL",
                "zone_id": "zone_b_concourse",
                "location_label": "Concourse B elevator B02",
                "associated_facility_id": "fac_elevator_b02",
                "latitude": 25.778150,
                "longitude": -80.191350,
                "bms_fault_code": "ERR_ELEV_MOTOR_OVERHEAT"
            }
        }
        res_naive = await ac.post("/api/v1/venues/venue_123/accessibility/barriers", json=barrier_payload_naive, headers=headers)
        assert res_naive.status_code == 422

        # 2. Test pagination limit validation (ge=1, le=100)
        res_limit_zero = await ac.get("/api/v1/venues/venue_123/accessibility/barriers?limit=0", headers=headers)
        assert res_limit_zero.status_code == 422
        
        res_limit_too_high = await ac.get("/api/v1/venues/venue_123/accessibility/barriers?limit=101", headers=headers)
        assert res_limit_too_high.status_code == 422

        res_offset_negative = await ac.get("/api/v1/venues/venue_123/accessibility/barriers?offset=-1", headers=headers)
        assert res_offset_negative.status_code == 422

        # 3. Test successful pagination query
        res_ok = await ac.get("/api/v1/venues/venue_123/accessibility/barriers?limit=5&offset=0", headers=headers)
        assert res_ok.status_code == 200
        assert isinstance(res_ok.json(), list)
