from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_
from typing import Optional, Tuple
from backend.app.models.volunteer import (
    Volunteer, VolunteerProfile, VolunteerTeam, VolunteerEmergencyContact,
    VolunteerStatus, Skill, VolunteerSkill, VolunteerCertification,
    VolunteerAvailability, VolunteerShift, VolunteerAssignment,
    VolunteerAttendance, VolunteerCheckIn, VolunteerCheckOut,
    VolunteerLocation, VolunteerAudit
)

class VolunteerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, volunteer_id: int) -> Optional[Volunteer]:
        stmt = select(Volunteer).where(
            Volunteer.id == volunteer_id,
            Volunteer.is_deleted == False
        ).options(
            selectinload(Volunteer.profile),
            selectinload(Volunteer.team),
            selectinload(Volunteer.skills_association).selectinload(VolunteerSkill.skill),
            selectinload(Volunteer.certifications),
            selectinload(Volunteer.availabilities),
            selectinload(Volunteer.emergency_contacts),
            selectinload(Volunteer.status_history),
            selectinload(Volunteer.user)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Optional[Volunteer]:
        stmt = select(Volunteer).where(
            Volunteer.user_id == user_id,
            Volunteer.is_deleted == False
        ).options(
            selectinload(Volunteer.profile),
            selectinload(Volunteer.team),
            selectinload(Volunteer.skills_association).selectinload(VolunteerSkill.skill),
            selectinload(Volunteer.certifications),
            selectinload(Volunteer.availabilities),
            selectinload(Volunteer.emergency_contacts),
            selectinload(Volunteer.status_history),
            selectinload(Volunteer.user)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Volunteer]:
        stmt = select(Volunteer).join(VolunteerProfile).where(
            VolunteerProfile.email == email,
            Volunteer.is_deleted == False
        ).options(
            selectinload(Volunteer.profile),
            selectinload(Volunteer.team),
            selectinload(Volunteer.skills_association).selectinload(VolunteerSkill.skill),
            selectinload(Volunteer.certifications),
            selectinload(Volunteer.availabilities),
            selectinload(Volunteer.emergency_contacts),
            selectinload(Volunteer.status_history),
            selectinload(Volunteer.user)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_volunteers(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str = None,
        team_id: int = None,
        search: str = None
    ) -> Tuple[list[Volunteer], int]:
        stmt = select(Volunteer).where(Volunteer.is_deleted == False)
        
        if status:
            stmt = stmt.where(Volunteer.status == status)
        if team_id:
            stmt = stmt.where(Volunteer.team_id == team_id)
        if search:
            stmt = stmt.join(VolunteerProfile).where(
                (VolunteerProfile.first_name.ilike(f"%{search}%")) |
                (VolunteerProfile.last_name.ilike(f"%{search}%")) |
                (VolunteerProfile.email.ilike(f"%{search}%"))
            )

        count_stmt = select(func.count(Volunteer.id)).where(Volunteer.is_deleted == False)
        if status:
            count_stmt = count_stmt.where(Volunteer.status == status)
        if team_id:
            count_stmt = count_stmt.where(Volunteer.team_id == team_id)
        if search:
            count_stmt = count_stmt.join(VolunteerProfile).where(
                (VolunteerProfile.first_name.ilike(f"%{search}%")) |
                (VolunteerProfile.last_name.ilike(f"%{search}%")) |
                (VolunteerProfile.email.ilike(f"%{search}%"))
            )

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.offset(offset).limit(limit).options(
            selectinload(Volunteer.profile),
            selectinload(Volunteer.team)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, volunteer: Volunteer) -> Volunteer:
        self.db.add(volunteer)
        await self.db.flush()
        return volunteer

    async def save(self, volunteer: Volunteer):
        await self.db.flush()

    async def commit(self):
        await self.db.commit()

    async def get_profile(self, volunteer_id: int) -> Optional[VolunteerProfile]:
        stmt = select(VolunteerProfile).where(
            VolunteerProfile.volunteer_id == volunteer_id,
            VolunteerProfile.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_profile(self, profile: VolunteerProfile) -> VolunteerProfile:
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def create_team(self, team: VolunteerTeam) -> VolunteerTeam:
        self.db.add(team)
        await self.db.flush()
        return team

    async def get_team(self, team_id: int) -> Optional[VolunteerTeam]:
        stmt = select(VolunteerTeam).where(
            VolunteerTeam.id == team_id,
            VolunteerTeam.is_deleted == False
        ).options(selectinload(VolunteerTeam.lead))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_teams(self, limit: int = 50, offset: int = 0) -> list[VolunteerTeam]:
        stmt = select(VolunteerTeam).where(VolunteerTeam.is_deleted == False).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_emergency_contact(self, contact: VolunteerEmergencyContact) -> VolunteerEmergencyContact:
        self.db.add(contact)
        await self.db.flush()
        return contact

    async def get_emergency_contacts(self, volunteer_id: int) -> list[VolunteerEmergencyContact]:
        stmt = select(VolunteerEmergencyContact).where(VolunteerEmergencyContact.volunteer_id == volunteer_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_status_log(self, status_log: VolunteerStatus) -> VolunteerStatus:
        self.db.add(status_log)
        await self.db.flush()
        return status_log


class SkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_skill_by_id(self, skill_id: int) -> Optional[Skill]:
        stmt = select(Skill).where(Skill.id == skill_id, Skill.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_skill_by_name(self, name: str) -> Optional[Skill]:
        stmt = select(Skill).where(Skill.name == name, Skill.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_skills(self, limit: int = 50, offset: int = 0) -> list[Skill]:
        stmt = select(Skill).where(Skill.is_deleted == False).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_skill(self, skill: Skill) -> Skill:
        self.db.add(skill)
        await self.db.flush()
        return skill

    async def add_volunteer_skill(self, volunteer_skill: VolunteerSkill) -> VolunteerSkill:
        self.db.add(volunteer_skill)
        await self.db.flush()
        return volunteer_skill

    async def get_volunteer_skills(self, volunteer_id: int) -> list[VolunteerSkill]:
        stmt = select(VolunteerSkill).where(VolunteerSkill.volunteer_id == volunteer_id).options(selectinload(VolunteerSkill.skill))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def remove_volunteer_skill(self, volunteer_id: int, skill_id: int):
        stmt = select(VolunteerSkill).where(
            VolunteerSkill.volunteer_id == volunteer_id,
            VolunteerSkill.skill_id == skill_id
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            await self.db.delete(record)
            await self.db.flush()

    async def create_certification(self, cert: VolunteerCertification) -> VolunteerCertification:
        self.db.add(cert)
        await self.db.flush()
        return cert

    async def get_certification(self, cert_id: int) -> Optional[VolunteerCertification]:
        stmt = select(VolunteerCertification).where(
            VolunteerCertification.id == cert_id,
            VolunteerCertification.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_certifications_by_volunteer(self, volunteer_id: int) -> list[VolunteerCertification]:
        stmt = select(VolunteerCertification).where(
            VolunteerCertification.volunteer_id == volunteer_id,
            VolunteerCertification.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_availability(self, availability: VolunteerAvailability) -> VolunteerAvailability:
        self.db.add(availability)
        await self.db.flush()
        return availability

    async def get_availabilities_by_volunteer(self, volunteer_id: int) -> list[VolunteerAvailability]:
        stmt = select(VolunteerAvailability).where(VolunteerAvailability.volunteer_id == volunteer_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def remove_availability(self, availability_id: int):
        stmt = select(VolunteerAvailability).where(VolunteerAvailability.id == availability_id)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            await self.db.delete(record)
            await self.db.flush()


class ShiftRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_shift_by_id(self, shift_id: int) -> Optional[VolunteerShift]:
        stmt = select(VolunteerShift).where(
            VolunteerShift.id == shift_id,
            VolunteerShift.is_deleted == False
        ).options(selectinload(VolunteerShift.assignments))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_shifts(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str = None,
        location_zone: str = None
    ) -> Tuple[list[VolunteerShift], int]:
        stmt = select(VolunteerShift).where(VolunteerShift.is_deleted == False)

        if status:
            stmt = stmt.where(VolunteerShift.status == status)
        if location_zone:
            stmt = stmt.where(VolunteerShift.location_zone == location_zone)

        count_stmt = select(func.count(VolunteerShift.id)).where(VolunteerShift.is_deleted == False)
        if status:
            count_stmt = count_stmt.where(VolunteerShift.status == status)
        if location_zone:
            count_stmt = count_stmt.where(VolunteerShift.location_zone == location_zone)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create_shift(self, shift: VolunteerShift) -> VolunteerShift:
        self.db.add(shift)
        await self.db.flush()
        return shift

    async def save_shift(self, shift: VolunteerShift):
        await self.db.flush()


class AssignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_assignment_by_id(self, assignment_id: int) -> Optional[VolunteerAssignment]:
        stmt = select(VolunteerAssignment).where(
            VolunteerAssignment.id == assignment_id,
            VolunteerAssignment.is_deleted == False
        ).options(
            selectinload(VolunteerAssignment.shift),
            selectinload(VolunteerAssignment.volunteer),
            selectinload(VolunteerAssignment.attendance),
            selectinload(VolunteerAssignment.check_ins),
            selectinload(VolunteerAssignment.check_outs)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_assignment_by_volunteer_and_shift(self, volunteer_id: int, shift_id: int) -> Optional[VolunteerAssignment]:
        stmt = select(VolunteerAssignment).where(
            VolunteerAssignment.volunteer_id == volunteer_id,
            VolunteerAssignment.shift_id == shift_id,
            VolunteerAssignment.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_assignments(
        self,
        limit: int = 50,
        offset: int = 0,
        volunteer_id: int = None,
        shift_id: int = None,
        status: str = None
    ) -> list[VolunteerAssignment]:
        stmt = select(VolunteerAssignment).where(VolunteerAssignment.is_deleted == False)

        if volunteer_id:
            stmt = stmt.where(VolunteerAssignment.volunteer_id == volunteer_id)
        if shift_id:
            stmt = stmt.where(VolunteerAssignment.shift_id == shift_id)
        if status:
            stmt = stmt.where(VolunteerAssignment.status == status)

        stmt = stmt.offset(offset).limit(limit).options(
            selectinload(VolunteerAssignment.shift),
            selectinload(VolunteerAssignment.volunteer)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_assignment(self, assignment: VolunteerAssignment) -> VolunteerAssignment:
        self.db.add(assignment)
        await self.db.flush()
        return assignment


class AttendanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_attendance_by_assignment(self, assignment_id: int) -> Optional[VolunteerAttendance]:
        stmt = select(VolunteerAttendance).where(VolunteerAttendance.assignment_id == assignment_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_attendance(self, attendance: VolunteerAttendance) -> VolunteerAttendance:
        self.db.add(attendance)
        await self.db.flush()
        return attendance

    async def create_check_in(self, check_in: VolunteerCheckIn) -> VolunteerCheckIn:
        self.db.add(check_in)
        await self.db.flush()
        return check_in

    async def create_check_out(self, check_out: VolunteerCheckOut) -> VolunteerCheckOut:
        self.db.add(check_out)
        await self.db.flush()
        return check_out

    async def get_check_ins_by_assignment(self, assignment_id: int) -> list[VolunteerCheckIn]:
        stmt = select(VolunteerCheckIn).where(VolunteerCheckIn.assignment_id == assignment_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_check_outs_by_assignment(self, assignment_id: int) -> list[VolunteerCheckOut]:
        stmt = select(VolunteerCheckOut).where(VolunteerCheckOut.assignment_id == assignment_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class LocationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_location(self, volunteer_id: int) -> Optional[VolunteerLocation]:
        stmt = select(VolunteerLocation).where(
            VolunteerLocation.volunteer_id == volunteer_id
        ).order_by(VolunteerLocation.updated_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_location(self, location: VolunteerLocation) -> VolunteerLocation:
        stmt = select(VolunteerLocation).where(
            VolunteerLocation.volunteer_id == location.volunteer_id
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.latitude = location.latitude
            existing.longitude = location.longitude
            existing.updated_at = location.updated_at
            await self.db.flush()
            return existing
        else:
            self.db.add(location)
            await self.db.flush()
            return location


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_audit(self, audit: VolunteerAudit) -> VolunteerAudit:
        self.db.add(audit)
        await self.db.flush()
        return audit

    async def list_audits(
        self,
        limit: int = 50,
        offset: int = 0,
        volunteer_id: int = None
    ) -> list[VolunteerAudit]:
        stmt = select(VolunteerAudit)
        if volunteer_id:
            stmt = stmt.where(
                (VolunteerAudit.target_type == 'Volunteer') &
                (VolunteerAudit.target_id == volunteer_id)
            )
        stmt = stmt.order_by(VolunteerAudit.timestamp.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
