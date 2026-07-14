import pytest
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.app.models.auth import Base, User
from backend.app.models.volunteer import (
    Volunteer, VolunteerProfile, VolunteerTeam, VolunteerEmergencyContact,
    VolunteerStatus, Skill, VolunteerSkill, VolunteerCertification,
    VolunteerAvailability, VolunteerShift, VolunteerAssignment,
    VolunteerAttendance, VolunteerCheckIn, VolunteerCheckOut,
    VolunteerLocation, VolunteerAudit
)
import backend.app.models.user_domain
from backend.app.services.validators import ValidationError
from backend.app.services.volunteer_service import (
    VolunteerService, SkillService, CertificationService,
    AvailabilityService, ShiftService, AssignmentService,
    AttendanceService, LocationService, AuditService
)

test_db_url = "sqlite+aiosqlite:///" + os.path.abspath("./test_volunteer_services.db").replace("\\", "/")
test_engine = create_async_engine(test_db_url, echo=False)
test_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="module", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    if os.path.exists("./test_volunteer_services.db"):
        try:
            os.remove("./test_volunteer_services.db")
        except Exception:
            pass

@pytest.fixture
async def db_session():
    async with test_session_maker() as session:
        yield session
        await session.rollback()

@pytest.mark.asyncio
async def test_volunteer_registration_and_validation(db_session: AsyncSession):
    # 1. Register base User
    user1 = User(email="jane.doe@aegis.com", hashed_password="pw", status="Active")
    db_session.add(user1)
    await db_session.flush()

    v_service = VolunteerService(db_session)
    
    # 2. Test valid registration
    profile_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@aegis.com",
        "phone": "+15551234567",
        "preferred_language": "en"
    }
    volunteer = await v_service.register_volunteer(user_id=user1.id, team_id=None, profile_data=profile_data)
    await db_session.commit()

    assert volunteer.status == "Pending"
    profile = await v_service.repo.get_profile(volunteer.id)
    assert profile is not None
    assert profile.first_name == "Jane"

    # 3. Test duplicate email registration
    user2 = User(email="jane.dup@aegis.com", hashed_password="pw", status="Active")
    db_session.add(user2)
    await db_session.flush()

    with pytest.raises(ValidationError) as excinfo:
        await v_service.register_volunteer(user_id=user2.id, team_id=None, profile_data=profile_data)
    assert "Email is already registered" in str(excinfo.value)

    # 4. Test invalid email format
    profile_data_invalid = profile_data.copy()
    profile_data_invalid["email"] = "invalid_email"
    with pytest.raises(ValidationError) as excinfo:
        await v_service.register_volunteer(user_id=user2.id, team_id=None, profile_data=profile_data_invalid)
    assert "Invalid email format" in str(excinfo.value)

@pytest.mark.asyncio
async def test_volunteer_status_transitions(db_session: AsyncSession):
    user = User(email="status@aegis.com", hashed_password="pw", status="Active")
    db_session.add(user)
    await db_session.flush()

    v_service = VolunteerService(db_session)
    profile_data = {"first_name": "John", "last_name": "Doe", "email": "status@aegis.com"}
    volunteer = await v_service.register_volunteer(user_id=user.id, team_id=None, profile_data=profile_data)
    await db_session.commit()

    # Initial is Pending. Pending -> Active is valid
    await v_service.update_status(volunteer.id, "Active", reason="Passed onboarding")
    assert volunteer.status == "Active"

    # Active -> OnShift is valid
    await v_service.update_status(volunteer.id, "OnShift", reason="Clocked in")
    assert volunteer.status == "OnShift"

    # OnShift -> Inactive is invalid (OnShift must go back to Active first)
    with pytest.raises(ValidationError):
        await v_service.update_status(volunteer.id, "Inactive", reason="Suspended")

@pytest.mark.asyncio
async def test_shift_assignments_and_overlaps(db_session: AsyncSession):
    user = User(email="assign@aegis.com", hashed_password="pw", status="Active")
    db_session.add(user)
    await db_session.flush()

    v_service = VolunteerService(db_session)
    profile_data = {"first_name": "Bob", "last_name": "Smith", "email": "assign@aegis.com"}
    volunteer = await v_service.register_volunteer(user_id=user.id, team_id=None, profile_data=profile_data)
    # Active status required for shifts
    await v_service.update_status(volunteer.id, "Active", "Activated")
    await db_session.commit()

    shift_service = ShiftService(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Create shift 1: 10:00 to 14:00
    shift1 = await shift_service.create_shift(
        name="Concourse Security",
        start_time=now + timedelta(hours=10),
        end_time=now + timedelta(hours=14),
        location_zone="Concourse A"
    )
    # Create shift 2: 12:00 to 16:00 (overlaps with shift 1)
    shift2 = await shift_service.create_shift(
        name="Queue Management",
        start_time=now + timedelta(hours=12),
        end_time=now + timedelta(hours=16),
        location_zone="Concourse B"
    )
    await db_session.commit()

    assign_service = AssignmentService(db_session)
    # Assign shift 1 (success)
    await assign_service.assign_shift(shift_id=shift1.id, volunteer_id=volunteer.id)
    await db_session.commit()

    # Assign shift 2 (should fail with overlap validation error)
    with pytest.raises(ValidationError) as excinfo:
        await assign_service.assign_shift(shift_id=shift2.id, volunteer_id=volunteer.id)
    assert "overlaps" in str(excinfo.value)

@pytest.mark.asyncio
async def test_attendance_checkin_checkout_sequence(db_session: AsyncSession):
    user = User(email="attend@aegis.com", hashed_password="pw", status="Active")
    db_session.add(user)
    await db_session.flush()

    v_service = VolunteerService(db_session)
    profile_data = {"first_name": "Alice", "last_name": "Jones", "email": "attend@aegis.com"}
    volunteer = await v_service.register_volunteer(user_id=user.id, team_id=None, profile_data=profile_data)
    await v_service.update_status(volunteer.id, "Active", "Activated")
    await db_session.commit()

    shift_service = ShiftService(db_session)
    shift = await shift_service.create_shift(
        name="Wayfinding",
        start_time=datetime.now(timezone.utc).replace(tzinfo=None),
        end_time=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=4),
        location_zone="Gate 4"
    )
    await db_session.commit()

    assign_service = AssignmentService(db_session)
    assignment = await assign_service.assign_shift(shift_id=shift.id, volunteer_id=volunteer.id)
    await db_session.commit()

    attend_service = AttendanceService(db_session)

    # Cannot check out before checking in
    with pytest.raises(ValidationError) as excinfo:
        await attend_service.check_out(assignment_id=assignment.id, verified_by_id=None, latitude=0.0, longitude=0.0)
    assert "Cannot check out before checking in" in str(excinfo.value)

    # Valid check in
    checkin = await attend_service.check_in(assignment_id=assignment.id, verified_by_id=None, latitude=25.77, longitude=-80.19)
    await db_session.commit()
    assert volunteer.status == "OnShift"

    # Cannot check in again
    with pytest.raises(ValidationError):
        await attend_service.check_in(assignment_id=assignment.id, verified_by_id=None, latitude=25.77, longitude=-80.19)

    # Valid check out
    await attend_service.check_out(assignment_id=assignment.id, verified_by_id=None, latitude=25.77, longitude=-80.19)
    await db_session.commit()
    assert volunteer.status == "Active"
