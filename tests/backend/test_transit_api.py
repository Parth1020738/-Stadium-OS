import pytest
import os
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.models.auth import Base, User
from backend.app.core.security import create_access_token
from backend.app.models.transit import TransitRoute, TransitStop, TransitVehicle, Driver, Operator, TransitOccupancy

import asyncio

test_db_url = "sqlite+aiosqlite:///" + os.path.abspath("./test_transit_api.db").replace("\\", "/")

@pytest.fixture(scope="module", autouse=True)
async def setup_api_db():
    os.environ["DATABASE_URL"] = test_db_url
    
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    import backend.app.models.user_domain
    import backend.app.models.transit
    from backend.app.core.dependencies import get_db_session
    
    api_test_engine = create_async_engine(test_db_url, echo=False)
    api_test_session = async_sessionmaker(api_test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with api_test_engine.begin() as conn:
        import backend.app.models.transit
        print("METADATA TABLES IN TEST:", list(Base.metadata.tables.keys()))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSession(api_test_engine) as session:
        stop = TransitStop(name="HUB_SOUTH", stop_code="HUB_SOUTH", latitude=25.2, longitude=51.5)
        driver = Driver(first_name="John", last_name="Doe", license_number="LIC-123", phone="555-0199", status="Active")
        vehicle = TransitVehicle(vehicle_code="V_BUS_MOCK", license_plate="ST-9922", vehicle_type="Bus", capacity=50, status="Active")
        session.add_all([stop, driver, vehicle])
        await session.flush()
        
        occupancy = TransitOccupancy(vehicle_id=vehicle.id, stop_id=stop.id, passenger_count=750)
        session.add(occupancy)
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
    if os.path.exists("./test_transit_api.db"):
        try:
            os.remove("./test_transit_api.db")
        except Exception:
            pass


@pytest.fixture(autouse=True)
async def mock_kafka_producer(monkeypatch):
    class MockKafkaProducer:
        async def start(self): pass
        async def stop(self): pass
        async def send_event(self, topic, key, value): return True
    mock = MockKafkaProducer()
    monkeypatch.setattr("backend.app.services.transit_service.kafka_producer", mock)
    monkeypatch.setattr("backend.app.main.kafka_producer", mock)


@pytest.mark.asyncio
async def test_transit_api_rbac_and_flow():
    # Setup tokens
    staff_token = create_access_token("9999", ["Staff"])
    headers_staff = {"Authorization": f"Bearer {staff_token}"}

    fan_token = create_access_token("8888", ["Fan"])
    headers_fan = {"Authorization": f"Bearer {fan_token}"}

    # Custom scope tokens
    token_payload_read = {"sub": "1001", "roles": ["Operator"], "scopes": ["transit:read"]}
    token_read = create_access_token("1001", ["Operator"])
    # Modify token to inject scopes for test
    from backend.app.core.security import settings
    import jwt
    secret = settings.JWT_SECRET
    alg = "HS256"
    
    jwt_read = jwt.encode({"sub": "1001", "roles": ["Operator"], "scopes": ["transit:read"], "jti": str(uuid.uuid4())}, secret, algorithm=alg)
    headers_read = {"Authorization": f"Bearer {jwt_read}"}

    jwt_write = jwt.encode({"sub": "1002", "roles": ["Operator"], "scopes": ["transit:write"], "jti": str(uuid.uuid4())}, secret, algorithm=alg)
    headers_write = {"Authorization": f"Bearer {jwt_write}"}

    jwt_pacing = jwt.encode({"sub": "1003", "roles": ["Operator"], "scopes": ["transit:pacing"], "jti": str(uuid.uuid4())}, secret, algorithm=alg)
    headers_pacing = {"Authorization": f"Bearer {jwt_pacing}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register Route (Staff only)
        route_payload = {
            "name": "Egress Shuttle Route 1",
            "route_code": "R_EGRESS_1",
            "route_type": "Shuttle",
            "description": "Stadium shuttle route"
        }
        res_r = await ac.post("/api/v1/transit/routes", json=route_payload, headers=headers_staff)
        assert res_r.status_code == 201
        route_id = res_r.json()["id"]

        # Register vehicle
        vehicle_payload = {
            "vehicle_code": "V_BUS_01",
            "license_plate": "ST-9922",
            "vehicle_type": "Bus",
            "capacity": 50
        }
        res_v = await ac.post("/api/v1/transit/vehicles", json=vehicle_payload, headers=headers_staff)
        assert res_v.status_code == 201
        vehicle_id = res_v.json()["id"]

        # Register schedule
        sched_payload = {
            "route_id": route_id,
            "day_of_week": 0,
            "departure_time": "18:00",
            "arrival_time": "18:30"
        }
        res_s = await ac.post("/api/v1/transit/schedules", json=sched_payload, headers=headers_staff)
        assert res_s.status_code == 201

        # Test overlap check (should fail)
        res_s_fail = await ac.post("/api/v1/transit/schedules", json=sched_payload, headers=headers_staff)
        assert res_s_fail.status_code == 400

        # Assign vehicle to route
        res_av = await ac.post("/api/v1/transit/assignments/vehicle", json={"vehicle_id": vehicle_id, "route_id": route_id}, headers=headers_staff)
        assert res_av.status_code == 201

        # Fetch driver from database to avoid hardcoded ID
        from sqlalchemy.future import select
        from backend.app.models.transit import Driver
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        engine = create_async_engine(test_db_url, echo=False)
        async with AsyncSession(engine) as session:
            result = await session.execute(select(Driver).where(Driver.license_number == "LIC-123"))
            driver_db = result.scalar_one()
            driver_id = driver_db.id

        # Assign driver to vehicle
        res_ad = await ac.post("/api/v1/transit/assignments/driver", json={"driver_id": driver_id, "vehicle_id": vehicle_id}, headers=headers_staff)
        assert res_ad.status_code == 201

        # Record Telemetry (Volunteer or Staff scope check)
        telemetry_payload = {
            "latitude": 25.22,
            "longitude": 51.52,
            "speed": 40.5,
            "heading": 90.0
        }
        res_tel = await ac.post(f"/api/v1/transit/vehicles/{vehicle_id}/telemetry", json=telemetry_payload, headers=headers_staff)
        assert res_tel.status_code == 200

        # 2. Get routes with transit:read scope
        res_list = await ac.get("/api/v1/transit/routes", headers=headers_read)
        assert res_list.status_code == 200
        assert len(res_list.json()["results"]) > 0

        # Get routes with Fan role (no transit:read scope) - should fail
        res_list_fail = await ac.get("/api/v1/transit/routes", headers=headers_fan)
        assert res_list_fail.status_code == 403

        # 3. Get hub occupancy (transit:read scope)
        res_occ = await ac.get("/api/v1/transit/hubs/HUB_SOUTH/occupancy", headers=headers_read)
        assert res_occ.status_code == 200
        assert res_occ.json()["hub_id"] == "HUB_SOUTH"

        # 4. Ingest alert (transit:write scope)
        alert_payload = {
            "traceId": "t-11",
            "correlationId": "c-11",
            "clientTimestamp": datetime.now(timezone.utc).isoformat(),
            "clientVersion": "1.0",
            "data": {
                "route_id": str(route_id),
                "hub_id": "HUB_SOUTH",
                "alert_type": "DIVERSION",
                "severity": "CRITICAL",
                "delay_minutes": 15,
                "reason": "Traffic incident on expressway"
            }
        }
        res_alert = await ac.post("/api/v1/transit/alerts", json=alert_payload, headers=headers_write)
        assert res_alert.status_code == 201
        assert res_alert.json()["data"]["status"] == "INGESTED"

        # Try alert with read-only token - should fail
        res_alert_fail = await ac.post("/api/v1/transit/alerts", json=alert_payload, headers=headers_read)
        assert res_alert_fail.status_code == 403

        # 5. Egress Pacing (transit:pacing scope)
        pacing_payload = {
            "traceId": "t-12",
            "correlationId": "c-12",
            "clientTimestamp": datetime.now(timezone.utc).isoformat(),
            "clientVersion": "1.0",
            "data": {
                "venue_id": "VENUE_STADIUM",
                "gate_ids": ["GATE_A", "GATE_B"],
                "pacing_rate_limit_per_minute": 120,
                "calculation_model": "EGRESS_SIMULATOR",
                "authorized_user_id": "1003"
            }
        }
        res_pace = await ac.post("/api/v1/transit/egress-pacing", json=pacing_payload, headers=headers_pacing)
        assert res_pace.status_code == 200
        assert len(res_pace.json()["data"]["gates_configured"]) == 2

        # Try pacing with write-only token - should fail
        res_pace_fail = await ac.post("/api/v1/transit/egress-pacing", json=pacing_payload, headers=headers_write)
        assert res_pace_fail.status_code == 403

        # 6. Statistics (Staff only)
        res_stats = await ac.get("/api/v1/transit/statistics", headers=headers_staff)
        assert res_stats.status_code == 200
        assert res_stats.json()["total_routes"] > 0


@pytest.mark.asyncio
async def test_concurrency_conflict_and_retry():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from backend.app.models.transit import ParkingZone
    from backend.app.services.transit_service import ParkingService
    
    engine = create_async_engine(test_db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSession(engine) as session:
        zone = ParkingZone(name="Zone Concurrency", total_spaces=100, occupied_spaces=10, location_zone="Zone A", status="Open")
        session.add(zone)
        await session.flush()
        zone_id = zone.id
        await session.commit()
        
    async with async_session() as session:
        service = ParkingService(session)
        updated_zone = await service.update_occupancy(zone_id=zone_id, occupied_spaces=20)
        assert updated_zone.occupied_spaces == 20
        assert updated_zone.version_id == 2


@pytest.mark.asyncio
async def test_unique_constraint_conflict_integrity_error(monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from backend.app.services.transit_service import RouteService
    from fastapi import HTTPException
    
    engine = create_async_engine(test_db_url, echo=False)
    
    async with AsyncSession(engine) as session:
        service = RouteService(session)
        await service.create_route(name="Route Unique", route_code="R_UNIQUE", route_type="Bus")
        
        async def mock_get_by_code(code):
            return None
        monkeypatch.setattr(service.repo, "get_by_code", mock_get_by_code)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.create_route(name="Route Unique Duplicate", route_code="R_UNIQUE", route_type="Bus")
        assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_kafka_rollback_on_failure(monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from backend.app.services.transit_service import RouteService
    
    class FailingMockKafkaProducer:
        async def start(self): pass
        async def stop(self): pass
        async def send_event(self, topic, key, value):
            raise RuntimeError("Kafka Broker Offline")
            
    monkeypatch.setattr("backend.app.services.transit_service.kafka_producer", FailingMockKafkaProducer())
    
    engine = create_async_engine(test_db_url, echo=False)
    async with AsyncSession(engine) as session:
        service = RouteService(session)
        
        with pytest.raises(Exception):
            await service.create_route(name="Route Kafka Fail", route_code="R_KAFKA_FAIL", route_type="Bus")
            
        await session.rollback()
        
    async with AsyncSession(engine) as session:
        service = RouteService(session)
        route = await service.repo.get_by_code("R_KAFKA_FAIL")
        assert route is None

