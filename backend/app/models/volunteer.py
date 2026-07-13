from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, Float
from sqlalchemy.orm import relationship as orm_relationship
from datetime import datetime, timezone
from backend.app.models.auth import Base

# Many-to-many relationship mapping volunteer to skills with additional info
class VolunteerSkill(Base):
    __tablename__ = "volunteer_skills"

    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    proficiency_level = Column(String(50), default="Intermediate") # Beginner, Intermediate, Expert

    volunteer = orm_relationship("Volunteer", back_populates="skills_association")
    skill = orm_relationship("Skill", back_populates="volunteers_association")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)

    volunteers_association = orm_relationship("VolunteerSkill", back_populates="skill", cascade="all, delete-orphan")


class VolunteerTeam(Base):
    __tablename__ = "volunteer_teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    lead_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    volunteers = orm_relationship("Volunteer", back_populates="team")
    lead = orm_relationship("User")


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    team_id = Column(Integer, ForeignKey("volunteer_teams.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="Pending", nullable=False) # Pending, Active, Inactive, OnShift

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    user = orm_relationship("User")
    team = orm_relationship("VolunteerTeam", back_populates="volunteers")
    profile = orm_relationship("VolunteerProfile", primaryjoin="and_(Volunteer.id==VolunteerProfile.volunteer_id, VolunteerProfile.is_deleted==False)", back_populates="volunteer", uselist=False, cascade="all, delete-orphan")
    skills_association = orm_relationship("VolunteerSkill", back_populates="volunteer", cascade="all, delete-orphan")
    certifications = orm_relationship("VolunteerCertification", primaryjoin="and_(Volunteer.id==VolunteerCertification.volunteer_id, VolunteerCertification.is_deleted==False)", back_populates="volunteer", cascade="all, delete-orphan")
    availabilities = orm_relationship("VolunteerAvailability", back_populates="volunteer", cascade="all, delete-orphan")
    assignments = orm_relationship("VolunteerAssignment", primaryjoin="and_(Volunteer.id==VolunteerAssignment.volunteer_id, VolunteerAssignment.is_deleted==False)", back_populates="volunteer", cascade="all, delete-orphan")
    locations = orm_relationship("VolunteerLocation", back_populates="volunteer", cascade="all, delete-orphan")
    status_history = orm_relationship("VolunteerStatus", back_populates="volunteer", cascade="all, delete-orphan")
    emergency_contacts = orm_relationship("VolunteerEmergencyContact", back_populates="volunteer", cascade="all, delete-orphan")


class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=False)
    preferred_language = Column(String(50), default="en", nullable=False)
    bio = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    volunteer = orm_relationship("Volunteer", back_populates="profile")


class VolunteerCertification(Base):
    __tablename__ = "volunteer_certifications"

    id = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    issuing_authority = Column(String(150), nullable=False)
    license_number = Column(String(100), nullable=True)
    issue_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    verification_status = Column(String(50), default="Pending") # Pending, Verified, Expired, Rejected

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    volunteer = orm_relationship("Volunteer", back_populates="certifications")


class VolunteerAvailability(Base):
    __tablename__ = "volunteer_availabilities"

    id = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=True) # 0-6 (Monday-Sunday)
    start_time = Column(String(10), nullable=False) # e.g. "08:00"
    end_time = Column(String(10), nullable=False) # e.g. "16:00"
    specific_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    volunteer = orm_relationship("Volunteer", back_populates="availabilities")


class VolunteerShift(Base):
    __tablename__ = "volunteer_shifts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location_zone = Column(String(100), nullable=False)
    required_skills = Column(Text, nullable=True) # Comma-separated or JSON
    status = Column(String(50), default="Scheduled") # Scheduled, Active, Completed, Cancelled

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    assignments = orm_relationship("VolunteerAssignment", back_populates="shift", cascade="all, delete-orphan")


class VolunteerAssignment(Base):
    __tablename__ = "volunteer_assignments"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("volunteer_shifts.id", ondelete="CASCADE"), nullable=False, index=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="Assigned") # Assigned, Accepted, Rejected, CheckedIn, Completed, Cancelled

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    shift = orm_relationship("VolunteerShift", back_populates="assignments")
    volunteer = orm_relationship("Volunteer", back_populates="assignments")
    attendance = orm_relationship("VolunteerAttendance", back_populates="assignment", uselist=False, cascade="all, delete-orphan")
    check_ins = orm_relationship("VolunteerCheckIn", back_populates="assignment", cascade="all, delete-orphan")
    check_outs = orm_relationship("VolunteerCheckOut", back_populates="assignment", cascade="all, delete-orphan")


class VolunteerAttendance(Base):
    __tablename__ = "volunteer_attendance"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("volunteer_assignments.id", ondelete="CASCADE"), unique=True, nullable=False)
    status = Column(String(50), default="Absent") # Present, Absent, Tardy
    checked_in_at = Column(DateTime, nullable=True)
    checked_out_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    assignment = orm_relationship("VolunteerAssignment", back_populates="attendance")


class VolunteerCheckIn(Base):
    __tablename__ = "volunteer_check_ins"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("volunteer_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    checked_in_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    verified_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    assignment = orm_relationship("VolunteerAssignment", back_populates="check_ins")
    verified_by = orm_relationship("User")


class VolunteerCheckOut(Base):
    __tablename__ = "volunteer_check_outs"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("volunteer_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    checked_out_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    verified_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    assignment = orm_relationship("VolunteerAssignment", back_populates="check_outs")
    verified_by = orm_relationship("User")


class VolunteerLocation(Base):
    __tablename__ = "volunteer_locations"

    id = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    volunteer = orm_relationship("Volunteer", back_populates="locations")


class VolunteerStatus(Base):
    __tablename__ = "volunteer_statuses"

    id = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    changed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=True)

    volunteer = orm_relationship("Volunteer", back_populates="status_history")
    changed_by = orm_relationship("User")


class VolunteerEmergencyContact(Base):
    __tablename__ = "volunteer_emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    relationship = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    volunteer = orm_relationship("Volunteer", back_populates="emergency_contacts")


class VolunteerAudit(Base):
    __tablename__ = "volunteer_audits"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_type = Column(String(50), nullable=False)
    target_id = Column(Integer, nullable=False)
    changes_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    actor = orm_relationship("User")
