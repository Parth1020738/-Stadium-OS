import json
import logging
import re
import uuid
from datetime import datetime, timezone, time, timedelta
from typing import Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError
from fastapi import HTTPException, status

from backend.app.services.validators import ValidationError
from backend.app.repositories.volunteer_repository import (
    VolunteerRepository, SkillRepository, ShiftRepository,
    AssignmentRepository, AttendanceRepository, LocationRepository,
    AuditRepository
)
from backend.app.models.volunteer import (
    Volunteer, VolunteerProfile, VolunteerTeam, VolunteerEmergencyContact,
    VolunteerStatus, Skill, VolunteerSkill, VolunteerCertification,
    VolunteerAvailability, VolunteerShift, VolunteerAssignment,
    VolunteerAttendance, VolunteerCheckIn, VolunteerCheckOut,
    VolunteerLocation, VolunteerAudit
)
from backend.app.core.kafka_producer import kafka_producer

logger = logging.getLogger("volunteer_service")

# Regex validators
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[\d\s\-()]{7,20}$")

def validate_email(email: str):
    if not EMAIL_REGEX.match(email):
        raise ValidationError({"email": "Invalid email format"})

def validate_phone(phone: Optional[str]):
    if phone and not PHONE_REGEX.match(phone):
        raise ValidationError({"phone": "Invalid phone number format"})


async def publish_kafka_event(topic: str, key: str, data: dict, correlation_id: Optional[str] = None):
    event_payload = {
        "schemaVersion": "1.0",
        "correlationId": correlation_id or f"corr-{uuid.uuid4()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }
    await kafka_producer.send_event(topic, key, event_payload)


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuditRepository(db)

    async def log_audit(
        self,
        action: str,
        actor_id: Optional[int],
        target_type: str,
        target_id: int,
        changes: Optional[dict] = None
    ) -> VolunteerAudit:
        safe_changes = {}
        if changes:
            for k, v in changes.items():
                if isinstance(v, datetime):
                    safe_changes[k] = v.isoformat()
                else:
                    safe_changes[k] = v

        audit = VolunteerAudit(
            action=action,
            actor_id=actor_id,
            target_type=target_type,
            target_id=target_id,
            changes_json=json.dumps(safe_changes) if safe_changes else None
        )
        await self.repo.create_audit(audit)

        log_payload = {
            "event": f"volunteer_{action.lower()}",
            "actor_id": actor_id,
            "target_type": target_type,
            "target_id": target_id,
            "changes": safe_changes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        logger.info(json.dumps(log_payload))
        return audit


class VolunteerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = VolunteerRepository(db)
        self.audit_service = AuditService(db)

    async def register_volunteer(
        self,
        user_id: int,
        team_id: Optional[int],
        profile_data: dict,
        actor_id: Optional[int] = None
    ) -> Volunteer:
        existing = await self.repo.get_by_user_id(user_id)
        if existing:
            raise ValidationError({"volunteer": "User is already registered as a volunteer"})

        email = profile_data.get("email")
        phone = profile_data.get("phone")

        if not email:
            raise ValidationError({"email": "Email is required"})
        validate_email(email)
        validate_phone(phone)

        dup_email = await self.repo.get_by_email(email)
        if dup_email:
            raise ValidationError({"email": "Email is already registered"})

        volunteer = Volunteer(
            user_id=user_id,
            team_id=team_id,
            status="Pending"
        )
        await self.repo.create(volunteer)

        profile = VolunteerProfile(
            volunteer_id=volunteer.id,
            first_name=profile_data.get("first_name", ""),
            last_name=profile_data.get("last_name", ""),
            phone=phone,
            email=email,
            preferred_language=profile_data.get("preferred_language", "en"),
            bio=profile_data.get("bio")
        )
        await self.repo.create_profile(profile)

        status_log = VolunteerStatus(
            volunteer_id=volunteer.id,
            status="Pending",
            reason="Initial registration",
            changed_by_id=actor_id
        )
        await self.repo.create_status_log(status_log)

        await self.audit_service.log_audit(
            action="CREATE",
            actor_id=actor_id,
            target_type="Volunteer",
            target_id=volunteer.id,
            changes={"status": "Pending", "email": email}
        )

        await publish_kafka_event(
            topic="volunteer.created",
            key=str(volunteer.id),
            data={
                "volunteer_id": volunteer.id,
                "user_id": user_id,
                "status": "Pending",
                "email": email,
                "first_name": profile.first_name,
                "last_name": profile.last_name
            }
        )

        return volunteer

    async def update_profile(
        self,
        volunteer_id: int,
        profile_data: dict,
        actor_id: Optional[int] = None
    ) -> VolunteerProfile:
        volunteer = await self.repo.get_by_id(volunteer_id)
        if not volunteer:
            raise HTTPException(status_code=404, detail="Volunteer not found")

        profile = volunteer.profile
        if not profile:
            raise HTTPException(status_code=404, detail="Volunteer profile not found")

        email = profile_data.get("email")
        phone = profile_data.get("phone")

        if email:
            validate_email(email)
            if email != profile.email:
                dup_email = await self.repo.get_by_email(email)
                if dup_email and dup_email.id != volunteer.id:
                    raise ValidationError({"email": "Email is already registered"})
                profile.email = email

        if phone:
            validate_phone(phone)
            profile.phone = phone

        if "first_name" in profile_data:
            profile.first_name = profile_data["first_name"]
        if "last_name" in profile_data:
            profile.last_name = profile_data["last_name"]
        if "preferred_language" in profile_data:
            profile.preferred_language = profile_data["preferred_language"]
        if "bio" in profile_data:
            profile.bio = profile_data["bio"]

        try:
            await self.repo.save(volunteer)
        except StaleDataError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Volunteer profile was modified by another transaction. Please reload."
            )

        await self.audit_service.log_audit(
            action="UPDATE_PROFILE",
            actor_id=actor_id,
            target_type="VolunteerProfile",
            target_id=profile.id,
            changes=profile_data
        )

        await publish_kafka_event(
            topic="volunteer.updated",
            key=str(volunteer_id),
            data={
                "volunteer_id": volunteer_id,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "phone": profile.phone,
                "email": profile.email
            }
        )

        return profile

    async def delete_volunteer(self, volunteer_id: int, actor_id: Optional[int] = None) -> None:
        volunteer = await self.repo.get_by_id(volunteer_id)
        if not volunteer:
            raise HTTPException(status_code=404, detail="Volunteer not found")

        volunteer.is_deleted = True
        if volunteer.profile:
            volunteer.profile.is_deleted = True

        try:
            await self.repo.save(volunteer)
        except StaleDataError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Volunteer was modified by another transaction. Please reload."
            )

        await self.audit_service.log_audit(
            action="DELETE",
            actor_id=actor_id,
            target_type="Volunteer",
            target_id=volunteer_id
        )

        await publish_kafka_event(
            topic="volunteer.deleted",
            key=str(volunteer_id),
            data={"volunteer_id": volunteer_id}
        )

    async def update_status(
        self,
        volunteer_id: int,
        target_status: str,
        reason: Optional[str],
        actor_id: Optional[int] = None
    ) -> Volunteer:
        volunteer = await self.repo.get_by_id(volunteer_id)
        if not volunteer:
            raise HTTPException(status_code=404, detail="Volunteer not found")

        valid_statuses = {"Pending", "Active", "Inactive", "OnShift"}
        if target_status not in valid_statuses:
            raise ValidationError({"status": f"Invalid status: {target_status}"})

        current_status = volunteer.status
        if current_status == target_status:
            return volunteer

        allowed = False
        if current_status == "Pending" and target_status in ("Active", "Inactive"):
            allowed = True
        elif current_status == "Active" and target_status in ("OnShift", "Inactive"):
            allowed = True
        elif current_status == "OnShift" and target_status == "Active":
            allowed = True
        elif current_status == "Inactive" and target_status == "Active":
            allowed = True

        if not allowed:
            raise ValidationError({"status": f"Status transition from {current_status} to {target_status} not allowed"})

        volunteer.status = target_status
        try:
            await self.repo.save(volunteer)
        except StaleDataError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Volunteer status was modified by another transaction. Please reload."
            )

        status_log = VolunteerStatus(
            volunteer_id=volunteer.id,
            status=target_status,
            reason=reason,
            changed_by_id=actor_id
        )
        await self.repo.create_status_log(status_log)

        await self.audit_service.log_audit(
            action="STATUS_CHANGE",
            actor_id=actor_id,
            target_type="Volunteer",
            target_id=volunteer.id,
            changes={"old_status": current_status, "new_status": target_status, "reason": reason}
        )

        await publish_kafka_event(
            topic="volunteer.status.changed",
            key=str(volunteer_id),
            data={
                "volunteer_id": volunteer_id,
                "old_status": current_status,
                "new_status": target_status,
                "reason": reason
            }
        )

        return volunteer

    async def update_emergency_contacts(
        self,
        volunteer_id: int,
        contacts_data: list[dict],
        actor_id: Optional[int] = None
    ) -> list[VolunteerEmergencyContact]:
        volunteer = await self.repo.get_by_id(volunteer_id)
        if not volunteer:
            raise HTTPException(status_code=404, detail="Volunteer not found")

        for c in contacts_data:
            validate_phone(c.get("phone"))
            if not c.get("name") or not c.get("relationship") or not c.get("phone"):
                raise ValidationError({"emergency_contact": "Name, relationship and phone are required"})

        existing_contacts = await self.repo.get_emergency_contacts(volunteer_id)
        for ec in existing_contacts:
            await self.db.delete(ec)

        new_contacts = []
        for c in contacts_data:
            contact = VolunteerEmergencyContact(
                volunteer_id=volunteer_id,
                name=c["name"],
                relationship=c["relationship"],
                phone=c["phone"],
                email=c.get("email"),
                notes=c.get("notes")
            )
            await self.repo.create_emergency_contact(contact)
            new_contacts.append(contact)

        await self.audit_service.log_audit(
            action="UPDATE_EMERGENCY_CONTACTS",
            actor_id=actor_id,
            target_type="Volunteer",
            target_id=volunteer_id
        )

        return new_contacts

    async def get_statistics(self) -> dict:
        total_stmt = select(func.count(Volunteer.id)).where(Volunteer.is_deleted == False)
        active_stmt = select(func.count(Volunteer.id)).where(Volunteer.is_deleted == False, Volunteer.status == "Active")
        onshift_stmt = select(func.count(Volunteer.id)).where(Volunteer.is_deleted == False, Volunteer.status == "OnShift")
        
        total_shifts_stmt = select(func.count(VolunteerShift.id)).where(VolunteerShift.is_deleted == False)
        completed_shifts_stmt = select(func.count(VolunteerShift.id)).where(VolunteerShift.is_deleted == False, VolunteerShift.status == "Completed")

        total_vol = (await self.db.execute(total_stmt)).scalar_one()
        active_vol = (await self.db.execute(active_stmt)).scalar_one()
        onshift_vol = (await self.db.execute(onshift_stmt)).scalar_one()
        
        total_shifts = (await self.db.execute(total_shifts_stmt)).scalar_one()
        completed_shifts = (await self.db.execute(completed_shifts_stmt)).scalar_one()

        # Attendance calculation
        present_stmt = select(func.count(VolunteerAttendance.id)).where(VolunteerAttendance.status.in_(["Present", "Tardy"]))
        total_att_stmt = select(func.count(VolunteerAttendance.id))
        
        present_count = (await self.db.execute(present_stmt)).scalar_one()
        total_att_count = (await self.db.execute(total_att_stmt)).scalar_one()

        att_rate = (present_count / total_att_count * 100.0) if total_att_count > 0 else 100.0

        return {
            "total_volunteers": total_vol,
            "active_volunteers": active_vol,
            "on_shift_volunteers": onshift_vol,
            "total_shifts": total_shifts,
            "completed_shifts": completed_shifts,
            "attendance_rate": round(att_rate, 2)
        }


class SkillService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SkillRepository(db)
        self.audit_service = AuditService(db)

    async def create_skill(self, name: str, description: Optional[str]) -> Skill:
        existing = await self.repo.get_skill_by_name(name)
        if existing:
            raise ValidationError({"name": "Skill name already exists"})

        skill = Skill(name=name, description=description)
        await self.repo.create_skill(skill)
        return skill

    async def assign_skill(self, volunteer_id: int, skill_id: int, proficiency_level: str, actor_id: Optional[int] = None) -> VolunteerSkill:
        valid_proficiencies = {"Beginner", "Intermediate", "Expert"}
        if proficiency_level not in valid_proficiencies:
            raise ValidationError({"proficiency_level": "Invalid proficiency level"})

        existing = await self.repo.get_volunteer_skills(volunteer_id)
        for s in existing:
            if s.skill_id == skill_id:
                raise ValidationError({"skill": "Skill already assigned to this volunteer"})

        vol_skill = VolunteerSkill(
            volunteer_id=volunteer_id,
            skill_id=skill_id,
            proficiency_level=proficiency_level
        )
        await self.repo.add_volunteer_skill(vol_skill)

        await self.audit_service.log_audit(
            action="ASSIGN_SKILL",
            actor_id=actor_id,
            target_type="Volunteer",
            target_id=volunteer_id,
            changes={"skill_id": skill_id, "proficiency": proficiency_level}
        )

        return vol_skill

    async def remove_skill(self, volunteer_id: int, skill_id: int, actor_id: Optional[int] = None):
        await self.repo.remove_volunteer_skill(volunteer_id, skill_id)
        await self.audit_service.log_audit(
            action="REMOVE_SKILL",
            actor_id=actor_id,
            target_type="Volunteer",
            target_id=volunteer_id,
            changes={"skill_id": skill_id}
        )


class CertificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SkillRepository(db)
        self.audit_service = AuditService(db)

    async def add_certification(self, volunteer_id: int, cert_data: dict, actor_id: Optional[int] = None) -> VolunteerCertification:
        expiry_date = cert_data.get("expiry_date")
        if expiry_date:
            if isinstance(expiry_date, str):
                expiry_date = datetime.fromisoformat(expiry_date)
            if expiry_date.tzinfo is not None:
                expiry_date = expiry_date.replace(tzinfo=None)

            if expiry_date < datetime.now(timezone.utc).replace(tzinfo=None):
                raise ValidationError({"expiry_date": "Certification has already expired"})

        issue_date = cert_data.get("issue_date")
        if isinstance(issue_date, str):
            issue_date = datetime.fromisoformat(issue_date)
        if issue_date and issue_date.tzinfo is not None:
            issue_date = issue_date.replace(tzinfo=None)

        if issue_date and expiry_date and issue_date > expiry_date:
            raise ValidationError({"issue_date": "Issue date must be before or equal to expiry date"})

        cert = VolunteerCertification(
            volunteer_id=volunteer_id,
            name=cert_data["name"],
            issuing_authority=cert_data["issuing_authority"],
            license_number=cert_data.get("license_number"),
            issue_date=issue_date or datetime.now(timezone.utc).replace(tzinfo=None),
            expiry_date=expiry_date,
            verification_status="Pending"
        )
        await self.repo.create_certification(cert)

        await self.audit_service.log_audit(
            action="ADD_CERTIFICATION",
            actor_id=actor_id,
            target_type="VolunteerCertification",
            target_id=cert.id,
            changes={"name": cert.name}
        )

        return cert

    async def verify_certification(self, cert_id: int, status: str, actor_id: Optional[int] = None) -> VolunteerCertification:
        cert = await self.repo.get_certification(cert_id)
        if not cert:
            raise HTTPException(status_code=404, detail="Certification not found")

        valid_statuses = {"Pending", "Verified", "Expired", "Rejected"}
        if status not in valid_statuses:
            raise ValidationError({"status": "Invalid certification status"})

        old_status = cert.verification_status
        cert.verification_status = status
        try:
            await self.db.flush()
        except StaleDataError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Certification was modified by another transaction. Please reload."
            )

        await self.audit_service.log_audit(
            action="VERIFY_CERTIFICATION",
            actor_id=actor_id,
            target_type="VolunteerCertification",
            target_id=cert_id,
            changes={"old_status": old_status, "new_status": status}
        )

        return cert


class AvailabilityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SkillRepository(db)

    async def add_availability(self, volunteer_id: int, avail_data: dict) -> VolunteerAvailability:
        day_of_week = avail_data.get("day_of_week")
        start_time = avail_data.get("start_time")
        end_time = avail_data.get("end_time")
        specific_date = avail_data.get("specific_date")

        if specific_date:
            if isinstance(specific_date, str):
                specific_date = datetime.fromisoformat(specific_date)
            if specific_date.tzinfo is not None:
                specific_date = specific_date.replace(tzinfo=None)

        time_regex = re.compile(r"^\d{2}:\d{2}$")
        if not time_regex.match(start_time) or not time_regex.match(end_time):
            raise ValidationError({"time": "Time must be in HH:MM format"})

        if start_time >= end_time:
            raise ValidationError({"time": "Start time must be before end time"})

        avail = VolunteerAvailability(
            volunteer_id=volunteer_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            specific_date=specific_date
        )
        await self.repo.create_availability(avail)
        return avail

    async def remove_availability(self, availability_id: int):
        await self.repo.remove_availability(availability_id)


class ShiftService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ShiftRepository(db)
        self.audit_service = AuditService(db)

    async def create_shift(
        self,
        name: str,
        start_time: datetime,
        end_time: datetime,
        location_zone: str,
        required_skills: Optional[str] = None,
        description: Optional[str] = None,
        actor_id: Optional[int] = None
    ) -> VolunteerShift:
        if start_time.tzinfo is not None:
            start_time = start_time.replace(tzinfo=None)
        if end_time.tzinfo is not None:
            end_time = end_time.replace(tzinfo=None)

        if start_time >= end_time:
            raise ValidationError({"start_time": "Start time must be before end time"})

        shift = VolunteerShift(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location_zone=location_zone,
            required_skills=required_skills,
            status="Scheduled"
        )
        await self.repo.create_shift(shift)

        await self.audit_service.log_audit(
            action="CREATE_SHIFT",
            actor_id=actor_id,
            target_type="VolunteerShift",
            target_id=shift.id,
            changes={"name": shift.name, "start_time": shift.start_time, "end_time": shift.end_time}
        )

        await publish_kafka_event(
            topic="volunteer.shift.created",
            key=str(shift.id),
            data={
                "shift_id": shift.id,
                "name": shift.name,
                "start_time": shift.start_time.isoformat(),
                "end_time": shift.end_time.isoformat(),
                "location_zone": shift.location_zone
            }
        )

        return shift

    async def update_shift_status(self, shift_id: int, status: str, actor_id: Optional[int] = None) -> VolunteerShift:
        shift = await self.repo.get_shift_by_id(shift_id)
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")

        valid_statuses = {"Scheduled", "Active", "Completed", "Cancelled"}
        if status not in valid_statuses:
            raise ValidationError({"status": "Invalid shift status"})

        old_status = shift.status
        shift.status = status
        try:
            await self.repo.save_shift(shift)
        except StaleDataError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Shift was modified by another transaction. Please reload."
            )

        await self.audit_service.log_audit(
            action="UPDATE_SHIFT_STATUS",
            actor_id=actor_id,
            target_type="VolunteerShift",
            target_id=shift_id,
            changes={"old_status": old_status, "new_status": status}
        )

        return shift


class AssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AssignmentRepository(db)
        self.shift_repo = ShiftRepository(db)
        self.volunteer_repo = VolunteerRepository(db)
        self.audit_service = AuditService(db)

    async def assign_shift(self, shift_id: int, volunteer_id: int, actor_id: Optional[int] = None) -> VolunteerAssignment:
        existing = await self.repo.get_assignment_by_volunteer_and_shift(volunteer_id, shift_id)
        if existing:
            raise ValidationError({"assignment": "Volunteer is already assigned to this shift"})

        shift = await self.shift_repo.get_shift_by_id(shift_id)
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")

        if shift.status in ("Completed", "Cancelled"):
            raise ValidationError({"shift": "Cannot assign to completed or cancelled shift"})

        assignments = await self.repo.list_assignments(volunteer_id=volunteer_id)
        for a in assignments:
            if a.shift.status not in ("Completed", "Cancelled"):
                if max(shift.start_time, a.shift.start_time) < min(shift.end_time, a.shift.end_time):
                    raise ValidationError({"overlap": f"Shift overlaps with existing assignment: {a.shift.name}"})

        volunteer = await self.volunteer_repo.get_by_id(volunteer_id)
        if not volunteer:
            raise HTTPException(status_code=404, detail="Volunteer not found")
        if volunteer.status == "Inactive":
            raise ValidationError({"volunteer": "Cannot assign shift to inactive volunteer"})

        # Check skill matching
        if shift.required_skills:
            req_skills = [s.strip().lower() for s in shift.required_skills.split(",") if s.strip()]
            if req_skills:
                vol_skills = [sa.skill.name.lower() for sa in volunteer.skills_association if sa.skill]
                missing = [s for s in req_skills if s not in vol_skills]
                if missing:
                    raise ValidationError({"skills": f"Volunteer lacks required skills: {', '.join(missing)}"})

        # Check availability matching
        if volunteer.availabilities:
            shift_date = shift.start_time.date()
            shift_weekday = shift.start_time.weekday()
            shift_start_str = shift.start_time.strftime("%H:%M")
            shift_end_str = shift.end_time.strftime("%H:%M")
            
            available = False
            for av in volunteer.availabilities:
                if av.specific_date:
                    if av.specific_date.date() == shift_date:
                        if av.start_time <= shift_start_str and av.end_time >= shift_end_str:
                            available = True
                            break
                elif av.day_of_week is not None:
                    if av.day_of_week == shift_weekday:
                        if av.start_time <= shift_start_str and av.end_time >= shift_end_str:
                            available = True
                            break
            
            if not available:
                raise ValidationError({"availability": "Volunteer is not available during this shift time"})

        assignment = VolunteerAssignment(
            shift_id=shift_id,
            volunteer_id=volunteer_id,
            status="Assigned"
        )
        await self.repo.create_assignment(assignment)

        await self.audit_service.log_audit(
            action="ASSIGN_SHIFT",
            actor_id=actor_id,
            target_type="VolunteerAssignment",
            target_id=assignment.id,
            changes={"shift_id": shift_id, "volunteer_id": volunteer_id}
        )

        await publish_kafka_event(
            topic="volunteer.shift.assigned",
            key=str(assignment.id),
            data={
                "assignment_id": assignment.id,
                "shift_id": shift_id,
                "volunteer_id": volunteer_id,
                "status": "Assigned"
            }
        )

        return assignment

    async def reassign_shift(self, assignment_id: int, new_volunteer_id: int, actor_id: Optional[int] = None) -> VolunteerAssignment:
        assignment = await self.repo.get_assignment_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        if assignment.status in ("CheckedIn", "Completed", "Cancelled"):
            raise ValidationError({"assignment": "Cannot reassign active, completed, or cancelled shift assignment"})

        old_volunteer_id = assignment.volunteer_id
        if old_volunteer_id == new_volunteer_id:
            return assignment

        new_volunteer = await self.volunteer_repo.get_by_id(new_volunteer_id)
        if not new_volunteer:
            raise HTTPException(status_code=404, detail="New volunteer not found")
        if new_volunteer.status == "Inactive":
            raise ValidationError({"volunteer": "Cannot assign shift to inactive volunteer"})

        # Check skill matching
        if assignment.shift.required_skills:
            req_skills = [s.strip().lower() for s in assignment.shift.required_skills.split(",") if s.strip()]
            if req_skills:
                vol_skills = [sa.skill.name.lower() for sa in new_volunteer.skills_association if sa.skill]
                missing = [s for s in req_skills if s not in vol_skills]
                if missing:
                    raise ValidationError({"skills": f"Volunteer lacks required skills: {', '.join(missing)}"})

        # Check availability matching
        if new_volunteer.availabilities:
            shift_date = assignment.shift.start_time.date()
            shift_weekday = assignment.shift.start_time.weekday()
            shift_start_str = assignment.shift.start_time.strftime("%H:%M")
            shift_end_str = assignment.shift.end_time.strftime("%H:%M")
            
            available = False
            for av in new_volunteer.availabilities:
                if av.specific_date:
                    if av.specific_date.date() == shift_date:
                        if av.start_time <= shift_start_str and av.end_time >= shift_end_str:
                            available = True
                            break
                elif av.day_of_week is not None:
                    if av.day_of_week == shift_weekday:
                        if av.start_time <= shift_start_str and av.end_time >= shift_end_str:
                            available = True
                            break
            
            if not available:
                raise ValidationError({"availability": "Volunteer is not available during this shift time"})

        existing = await self.repo.get_assignment_by_volunteer_and_shift(new_volunteer_id, assignment.shift_id)
        if existing:
            raise ValidationError({"assignment": "New volunteer is already assigned to this shift"})

        assignments = await self.repo.list_assignments(volunteer_id=new_volunteer_id)
        for a in assignments:
            if a.shift.status not in ("Completed", "Cancelled"):
                if max(assignment.shift.start_time, a.shift.start_time) < min(assignment.shift.end_time, a.shift.end_time):
                    raise ValidationError({"overlap": f"Shift overlaps with existing assignment for new volunteer: {a.shift.name}"})

        assignment.volunteer_id = new_volunteer_id
        try:
            await self.db.flush()
        except StaleDataError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Assignment was modified by another transaction. Please reload."
            )

        await self.audit_service.log_audit(
            action="REASSIGN_SHIFT",
            actor_id=actor_id,
            target_type="VolunteerAssignment",
            target_id=assignment_id,
            changes={"old_volunteer_id": old_volunteer_id, "new_volunteer_id": new_volunteer_id}
        )

        await publish_kafka_event(
            topic="volunteer.shift.reassigned",
            key=str(assignment_id),
            data={
                "assignment_id": assignment_id,
                "old_volunteer_id": old_volunteer_id,
                "new_volunteer_id": new_volunteer_id
            }
        )

        return assignment


class AttendanceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AttendanceRepository(db)
        self.assign_repo = AssignmentRepository(db)
        self.volunteer_repo = VolunteerRepository(db)
        self.audit_service = AuditService(db)

    async def check_in(
        self,
        assignment_id: int,
        verified_by_id: Optional[int],
        latitude: Optional[float],
        longitude: Optional[float],
        notes: Optional[str] = None,
        actor_id: Optional[int] = None
    ) -> VolunteerCheckIn:
        assignment = await self.assign_repo.get_assignment_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        if assignment.status == "CheckedIn":
            raise ValidationError({"checkin": "Volunteer is already checked in"})

        if assignment.status in ("Completed", "Cancelled"):
            raise ValidationError({"checkin": "Cannot check in to completed or cancelled assignment"})

        assignment.status = "CheckedIn"
        
        volunteer = await self.volunteer_repo.get_by_id(assignment.volunteer_id)
        if volunteer:
            volunteer.status = "OnShift"

        checkin_time = datetime.now(timezone.utc).replace(tzinfo=None)
        check_in = VolunteerCheckIn(
            assignment_id=assignment_id,
            checked_in_at=checkin_time,
            verified_by_id=verified_by_id,
            latitude=latitude,
            longitude=longitude,
            notes=notes
        )
        await self.repo.create_check_in(check_in)

        attendance = await self.repo.get_attendance_by_assignment(assignment_id)
        
        shift_start = assignment.shift.start_time
        status = "Present"
        if checkin_time > shift_start + timedelta(minutes=15):
            status = "Tardy"

        if attendance:
            attendance.status = status
            attendance.checked_in_at = checkin_time
        else:
            attendance = VolunteerAttendance(
                assignment_id=assignment_id,
                status=status,
                checked_in_at=checkin_time
            )
            await self.repo.create_attendance(attendance)

        await self.audit_service.log_audit(
            action="CHECKIN",
            actor_id=actor_id,
            target_type="VolunteerAssignment",
            target_id=assignment_id,
            changes={"status": status, "checked_in_at": checkin_time}
        )

        await publish_kafka_event(
            topic="volunteer.checkin",
            key=str(assignment_id),
            data={
                "assignment_id": assignment_id,
                "volunteer_id": assignment.volunteer_id,
                "checked_in_at": checkin_time.isoformat(),
                "latitude": latitude,
                "longitude": longitude
            }
        )

        await publish_kafka_event(
            topic="volunteer.attendance.updated",
            key=str(assignment_id),
            data={
                "assignment_id": assignment_id,
                "volunteer_id": assignment.volunteer_id,
                "status": status,
                "checked_in_at": checkin_time.isoformat()
            }
        )

        return check_in

    async def check_out(
        self,
        assignment_id: int,
        verified_by_id: Optional[int],
        latitude: Optional[float],
        longitude: Optional[float],
        notes: Optional[str] = None,
        actor_id: Optional[int] = None
    ) -> VolunteerCheckOut:
        assignment = await self.assign_repo.get_assignment_by_id(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        if assignment.status != "CheckedIn":
            raise ValidationError({"checkout": "Cannot check out before checking in"})

        assignment.status = "Completed"

        volunteer = await self.volunteer_repo.get_by_id(assignment.volunteer_id)
        if volunteer:
            volunteer.status = "Active"

        checkout_time = datetime.now(timezone.utc).replace(tzinfo=None)
        check_out = VolunteerCheckOut(
            assignment_id=assignment_id,
            checked_out_at=checkout_time,
            verified_by_id=verified_by_id,
            latitude=latitude,
            longitude=longitude,
            notes=notes
        )
        await self.repo.create_check_out(check_out)

        attendance = await self.repo.get_attendance_by_assignment(assignment_id)
        if attendance:
            attendance.checked_out_at = checkout_time
        else:
            attendance = VolunteerAttendance(
                assignment_id=assignment_id,
                status="Present",
                checked_out_at=checkout_time
            )
            await self.repo.create_attendance(attendance)

        await self.audit_service.log_audit(
            action="CHECKOUT",
            actor_id=actor_id,
            target_type="VolunteerAssignment",
            target_id=assignment_id,
            changes={"checked_out_at": checkout_time}
        )

        await publish_kafka_event(
            topic="volunteer.checkout",
            key=str(assignment_id),
            data={
                "assignment_id": assignment_id,
                "volunteer_id": assignment.volunteer_id,
                "checked_out_at": checkout_time.isoformat(),
                "latitude": latitude,
                "longitude": longitude
            }
        )

        await publish_kafka_event(
            topic="volunteer.attendance.updated",
            key=str(assignment_id),
            data={
                "assignment_id": assignment_id,
                "volunteer_id": assignment.volunteer_id,
                "status": attendance.status if attendance else "Present",
                "checked_in_at": attendance.checked_in_at.isoformat() if (attendance and attendance.checked_in_at) else None,
                "checked_out_at": checkout_time.isoformat()
            }
        )

        return check_out


class LocationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LocationRepository(db)

    async def update_location(self, volunteer_id: int, latitude: float, longitude: float) -> VolunteerLocation:
        location = VolunteerLocation(
            volunteer_id=volunteer_id,
            latitude=latitude,
            longitude=longitude,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        return await self.repo.update_location(location)
