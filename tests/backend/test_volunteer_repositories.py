import pytest
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import StaleDataError

from backend.app.models.auth import Base, User
import backend.app.models.user_domain
from backend.app.models.volunteer import (
    Volunteer, VolunteerProfile, VolunteerTeam, VolunteerEmergencyContact,
    VolunteerStatus, Skill, VolunteerSkill, VolunteerCertification,
    VolunteerAvailability, VolunteerShift, VolunteerAssignment,
    VolunteerAttendance, VolunteerCheckIn, VolunteerCheckOut,
    VolunteerLocation, VolunteerAudit
)
from backend.app.repositories.volunteer_repository import (
    VolunteerRepository, SkillRepository, ShiftRepository,
    AssignmentRepository, AttendanceRepository, LocationRepository,
    AuditRepository
)

# Setup test DB connection string
test_db_url = "sqlite+aiosqlite:///./test_volunteer_repos.db"
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
    if os.path.exists("./test_volunteer_repos.db"):
        try:
            os.remove("./test_volunteer_repos.db")
        except Exception:
            pass

@pytest.fixture
async def db_session():
    async with test_session_maker() as session:
        yield session
        await session.rollback()

@pytest.mark.asyncio
async def test_volunteer_crud_and_optimistic_locking(db_session: AsyncSession):
    # 1. Create a User first
    user = User(email="volunteer_test@aegis.com", hashed_password="hashed_password", status="Active")
    db_session.add(user)
    await db_session.flush()

    # 2. Create VolunteerTeam
    volunteer_team = VolunteerTeam(name="First Aid Team", description="Handles spectator medical aid")
    db_session.add(volunteer_team)
    await db_session.flush()

    # 3. Create Volunteer linked to User and Team
    volunteer = Volunteer(user_id=user.id, team_id=volunteer_team.id, status="Active")
    volunteer_repo = VolunteerRepository(db_session)
    await volunteer_repo.create(volunteer)

    # 4. Create VolunteerProfile
    profile = VolunteerProfile(
        volunteer_id=volunteer.id,
        first_name="Jane",
        last_name="Doe",
        phone="555-0199",
        email="volunteer_test@aegis.com",
        preferred_language="en",
        bio="Experienced emergency responder"
    )
    await volunteer_repo.create_profile(profile)
    await db_session.commit()

    # 5. Read and Verify
    fetched = await volunteer_repo.get_by_id(volunteer.id)
    assert fetched is not None
    assert fetched.profile.first_name == "Jane"
    assert fetched.team.name == "First Aid Team"

    # 6. Test Optimistic Locking
    # Modify fetched object on session 1
    fetched.status = "OnShift"
    
    # Open another session to modify the same row in parallel
    async with test_session_maker() as session2:
        v_repo2 = VolunteerRepository(session2)
        fetched2 = await v_repo2.get_by_id(volunteer.id)
        assert fetched2 is not None
        fetched2.status = "Inactive"
        await session2.commit() # Increments version_id from 1 to 2

    # Attempting to commit session 1 should fail with StaleDataError/OptimisticLocking error
    with pytest.raises(StaleDataError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_skills_and_certifications(db_session: AsyncSession):
    # Setup User and Volunteer
    user = User(email="volunteer_skills@aegis.com", hashed_password="hashed_password", status="Active")
    db_session.add(user)
    await db_session.flush()
    volunteer = Volunteer(user_id=user.id, status="Active")
    db_session.add(volunteer)
    await db_session.flush()

    skill_repo = SkillRepository(db_session)
    # Create a Skill
    skill = Skill(name="CPR Certification", description="Cardiopulmonary Resuscitation")
    await skill_repo.create_skill(skill)
    await db_session.commit()

    # Associate Skill with Volunteer
    vol_skill = VolunteerSkill(volunteer_id=volunteer.id, skill_id=skill.id, proficiency_level="Expert")
    await skill_repo.add_volunteer_skill(vol_skill)
    await db_session.commit()

    # Verify Skill
    skills = await skill_repo.get_volunteer_skills(volunteer.id)
    assert len(skills) == 1
    assert skills[0].skill.name == "CPR Certification"
    assert skills[0].proficiency_level == "Expert"

    # Create Certification
    cert = VolunteerCertification(
        volunteer_id=volunteer.id,
        name="Red Cross CPR",
        issuing_authority="American Red Cross",
        license_number="CPR-12345",
        issue_date=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30),
        expiry_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=335),
        verification_status="Verified"
    )
    await skill_repo.create_certification(cert)
    await db_session.commit()

    certs = await skill_repo.get_certifications_by_volunteer(volunteer.id)
    assert len(certs) == 1
    assert certs[0].license_number == "CPR-12345"

@pytest.mark.asyncio
async def test_shifts_and_assignments(db_session: AsyncSession):
    # Setup User and Volunteer
    user = User(email="volunteer_shifts@aegis.com", hashed_password="hashed_password", status="Active")
    db_session.add(user)
    await db_session.flush()
    volunteer = Volunteer(user_id=user.id, status="Active")
    db_session.add(volunteer)
    await db_session.flush()

    shift_repo = ShiftRepository(db_session)
    # Create VolunteerShift
    shift = VolunteerShift(
        name="Morning Ingress Support",
        description="Support spectators checking in",
        start_time=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=2),
        end_time=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=6),
        location_zone="Zone A Gate 1",
        status="Scheduled"
    )
    await shift_repo.create_shift(shift)
    await db_session.commit()

    # Create VolunteerAssignment
    assign_repo = AssignmentRepository(db_session)
    assignment = VolunteerAssignment(
        shift_id=shift.id,
        volunteer_id=volunteer.id,
        status="Assigned"
    )
    await assign_repo.create_assignment(assignment)
    await db_session.commit()

    # Verify Assignment
    fetched_assign = await assign_repo.get_assignment_by_volunteer_and_shift(volunteer.id, shift.id)
    assert fetched_assign is not None
    assert fetched_assign.status == "Assigned"

@pytest.mark.asyncio
async def test_attendance_checkin_checkout(db_session: AsyncSession):
    # Setup
    user = User(email="volunteer_attendance@aegis.com", hashed_password="hashed_password", status="Active")
    db_session.add(user)
    await db_session.flush()
    volunteer = Volunteer(user_id=user.id, status="Active")
    db_session.add(volunteer)
    await db_session.flush()
    shift = VolunteerShift(
        name="Night Shift",
        start_time=datetime.now(timezone.utc).replace(tzinfo=None),
        end_time=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=4),
        location_zone="Zone B"
    )
    db_session.add(shift)
    await db_session.flush()
    assignment = VolunteerAssignment(shift_id=shift.id, volunteer_id=volunteer.id, status="Assigned")
    db_session.add(assignment)
    await db_session.flush()
    await db_session.commit()

    attendance_repo = AttendanceRepository(db_session)

    # 1. Create Attendance record
    attendance = VolunteerAttendance(assignment_id=assignment.id, status="Present", checked_in_at=datetime.now(timezone.utc).replace(tzinfo=None))
    await attendance_repo.create_attendance(attendance)
    await db_session.commit()

    # 2. Check In Log
    checkin = VolunteerCheckIn(assignment_id=assignment.id, checked_in_at=datetime.now(timezone.utc).replace(tzinfo=None), latitude=25.7749, longitude=-80.1918)
    await attendance_repo.create_check_in(checkin)
    await db_session.commit()

    # 3. Check Out Log
    checkout = VolunteerCheckOut(assignment_id=assignment.id, checked_out_at=datetime.now(timezone.utc).replace(tzinfo=None), latitude=25.7749, longitude=-80.1918)
    await attendance_repo.create_check_out(checkout)
    await db_session.commit()

    # 4. Verify Attendance and Check In/Out
    fetched_att = await attendance_repo.get_attendance_by_assignment(assignment.id)
    assert fetched_att is not None
    assert fetched_att.status == "Present"

    checkins = await attendance_repo.get_check_ins_by_assignment(assignment.id)
    assert len(checkins) == 1
    assert checkins[0].latitude == 25.7749
