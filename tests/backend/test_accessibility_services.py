import pytest
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.models.auth import Base
import backend.app.models.user_domain
from backend.app.models.accessibility import AccessibilityFacility, AccessibilityMap, AccessibilityBarrier
from backend.app.services.accessibility_service import AccessibilityService
from backend.app.services.validators import ValidationError

test_db_url = "sqlite+aiosqlite:///./test_accessibility_services.db"

@pytest.fixture(autouse=True)
async def setup_db():
    os.environ["DATABASE_URL"] = test_db_url
    engine = create_async_engine(test_db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if os.path.exists("./test_accessibility_services.db"):
        try:
            os.remove("./test_accessibility_services.db")
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


@pytest.mark.asyncio
async def test_barrier_registration_and_validation(setup_db):
    async_session = setup_db
    async with async_session() as session:
        service = AccessibilityService(session)

        # Invalid Severity Check
        with pytest.raises(ValidationError) as exc:
            await service.register_barrier("venue_1", "ELEVATOR_OUTAGE", "SUPER_CRITICAL", "zone_a", "label", 0.0, 0.0)
        assert "severity" in exc.value.errors

        # Invalid Coordinates Check
        with pytest.raises(ValidationError) as exc:
            await service.register_barrier("venue_1", "ELEVATOR_OUTAGE", "CRITICAL", "zone_a", "label", 100.0, 200.0)
        assert "coordinates" in exc.value.errors

        # Successful registration
        barrier = await service.register_barrier("venue_1", "ELEVATOR_OUTAGE", "CRITICAL", "zone_a", "label", 25.0, -80.0)
        assert barrier.id is not None
        assert barrier.status == "Active"

        # Duplicate barrier detection check
        with pytest.raises(ValidationError) as exc:
            await service.register_barrier("venue_1", "ELEVATOR_OUTAGE", "CRITICAL", "zone_a", "label", 25.0, -80.0)
        assert "barrier" in exc.value.errors


@pytest.mark.asyncio
async def test_route_generation_and_validations(setup_db):
    async_session = setup_db
    async with async_session() as session:
        service = AccessibilityService(session)

        # Missing Map Check
        with pytest.raises(ValidationError) as exc:
            await service.generate_route("venue_1", "zone_start", "zone_end", "WHEELCHAIR")
        assert "map" in exc.value.errors

        # Create active map layout
        acc_map = AccessibilityMap(venue_id="venue_1", status="Active")
        session.add(acc_map)
        await session.flush()

        # Route cycles/loops check
        with pytest.raises(ValidationError) as exc:
            await service.generate_route("venue_1", "zone_start", "zone_start", "WHEELCHAIR")
        assert "route" in exc.value.errors

        # Successful Route generation
        route = await service.generate_route("venue_1", "zone_start", "zone_end", "WHEELCHAIR")
        assert route.id is not None
        db_route = await service.route_repo.get_by_id(route.id)
        assert len(db_route.waypoints) == 2


@pytest.mark.asyncio
async def test_temporary_barrier_expiration(setup_db):
    async_session = setup_db
    async with async_session() as session:
        service = AccessibilityService(session)
        
        # Register temporary barrier that has already expired
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        barrier = AccessibilityBarrier(
            venue_id="venue_1",
            barrier_type="RAMP_CLOSED",
            severity="MINOR",
            zone_id="zone_temp",
            location_label="Temp ramp",
            latitude=25.0,
            longitude=-80.0,
            status="Active",
            expires_at=expired_time.replace(tzinfo=None)
        )
        session.add(barrier)
        await session.commit()

        await service.check_temporary_expirations()
        await session.refresh(barrier)
        assert barrier.status == "Expired"
        assert barrier.is_deleted == True
