import pytest
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm.exc import StaleDataError
from backend.app.models.auth import Base, User
import backend.app.models.user_domain
from backend.app.models.accessibility import (
    AccessibilityBarrier,
    AccessibilityRoute,
    AccessibilityWaypoint,
    AccessibilityFacility,
    AccessibilityMap,
    AccessibilityAlert,
    AccessibilityAudit
)
from backend.app.repositories.accessibility_repository import (
    AccessibilityBarrierRepository,
    AccessibilityRouteRepository,
    AccessibilityMapRepository,
    AccessibilityFacilityRepository,
    AccessibilityAlertRepository,
    AccessibilityAuditRepository
)

test_db_url = "sqlite+aiosqlite:///./test_accessibility_repos.db"

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
    if os.path.exists("./test_accessibility_repos.db"):
        try:
            os.remove("./test_accessibility_repos.db")
        except Exception:
            pass


@pytest.mark.asyncio
async def test_barrier_repository_crud_and_soft_delete(setup_db):
    async_session = setup_db
    async with async_session() as session:
        barrier_repo = AccessibilityBarrierRepository(session)
        barrier = AccessibilityBarrier(
            venue_id="venue_1",
            barrier_type="ELEVATOR_OUTAGE",
            severity="CRITICAL",
            zone_id="zone_a",
            location_label="Concourse A elevator",
            latitude=25.778,
            longitude=-80.191,
            status="Active"
        )
        await barrier_repo.create(barrier)
        await session.commit()

        # Get by ID
        db_barrier = await barrier_repo.get_by_id(barrier.id)
        assert db_barrier is not None
        assert db_barrier.barrier_type == "ELEVATOR_OUTAGE"

        # List by Venue
        barriers = await barrier_repo.list_by_venue("venue_1")
        assert len(barriers) == 1

        # Update & Concurrency Check
        db_barrier.location_label = "Updated concourse elevator"
        await session.commit()

        # Stale data concurrency test
        async with async_session() as session2:
            barrier_repo2 = AccessibilityBarrierRepository(session2)
            barrier2 = await barrier_repo2.get_by_id(barrier.id)
            barrier2.location_label = "Concurrent update"
            
            db_barrier.location_label = "Original update"
            await session.commit()
            
            with pytest.raises(StaleDataError):
                await session2.commit()

        # Soft Delete
        db_barrier.is_deleted = True
        await session.commit()

        deleted_barrier = await barrier_repo.get_by_id(barrier.id)
        assert deleted_barrier is None
