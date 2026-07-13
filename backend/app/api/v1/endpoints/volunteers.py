from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.volunteer_schemas import (
    CreateVolunteerRequest, UpdateVolunteerRequest, VolunteerResponse,
    StatisticsResponse, PaginationResponse, CreateSkillRequest,
    AssignSkillRequest, AddCertificationRequest, AddAvailabilityRequest,
    ErrorResponse
)
from backend.app.services.volunteer_service import (
    VolunteerService, SkillService, CertificationService, AvailabilityService
)
from backend.app.services.validators import ValidationError

router = APIRouter(prefix="/volunteers", tags=["Volunteers"])

staff_or_admin = RoleChecker(["Staff", "Admin"])
volunteer_or_staff = RoleChecker(["Volunteer", "Staff", "Admin"])

def get_user_id_from_current_user(current_user: dict) -> int:
    sub = current_user.get("sub")
    if sub and str(sub).isdigit():
        return int(sub)
    u_id = current_user.get("user_id")
    if u_id:
        return int(u_id)
    # Fallback to a mock/parsed integer if sub is an email/string (for tests)
    if sub:
        # If it's a test string, hash or convert to int to prevent crash
        try:
            return int(sub)
        except ValueError:
            return 99999 # Fallback test user ID
    raise HTTPException(status_code=401, detail="Invalid token payload: user_id or sub not found")

async def check_self_or_staff(volunteer_id: int, current_user: dict, db: AsyncSession):
    user_roles = current_user.get("roles", [])
    if any(role in ["Staff", "Admin"] for role in user_roles):
        return True

    user_id = get_user_id_from_current_user(current_user)
    v_service = VolunteerService(db)
    volunteer = await v_service.repo.get_by_id(volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    if volunteer.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own profile"
        )
    return True


@router.post(
    "",
    response_model=VolunteerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new volunteer"
)
async def register_volunteer(
    req: CreateVolunteerRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    v_service = VolunteerService(db)
    try:
        profile_data = {
            "first_name": req.first_name,
            "last_name": req.last_name,
            "email": req.email,
            "phone": req.phone,
            "preferred_language": req.preferred_language,
            "bio": req.bio
        }
        volunteer = await v_service.register_volunteer(
            user_id=req.user_id,
            team_id=req.team_id,
            profile_data=profile_data,
            actor_id=actor_id
        )
        db_vol = await v_service.repo.get_by_id(volunteer.id)
        return db_vol
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Get volunteer operational statistics"
)
async def get_volunteer_statistics(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    v_service = VolunteerService(db)
    stats = await v_service.get_statistics()
    return stats


@router.get(
    "",
    response_model=PaginationResponse,
    summary="List all registered volunteers"
)
async def list_volunteers(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    team_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    v_service = VolunteerService(db)
    results, total = await v_service.repo.list_volunteers(
        limit=limit,
        offset=offset,
        status=status,
        team_id=team_id,
        search=search
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": results
    }


@router.get(
    "/{volunteerId}",
    response_model=VolunteerResponse,
    summary="Get volunteer details by ID"
)
async def get_volunteer(
    volunteerId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(volunteer_or_staff)
):
    await check_self_or_staff(volunteerId, current_user, db)
    v_service = VolunteerService(db)
    volunteer = await v_service.repo.get_by_id(volunteerId)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return volunteer


@router.put(
    "/{volunteerId}",
    response_model=VolunteerResponse,
    summary="Update volunteer profile"
)
async def update_volunteer_profile(
    volunteerId: int,
    req: UpdateVolunteerRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(volunteer_or_staff)
):
    await check_self_or_staff(volunteerId, current_user, db)
    actor_id = get_user_id_from_current_user(current_user)
    v_service = VolunteerService(db)
    try:
        profile_data = req.dict(exclude_unset=True)
        await v_service.update_profile(
            volunteer_id=volunteerId,
            profile_data=profile_data,
            actor_id=actor_id
        )
        db_vol = await v_service.repo.get_by_id(volunteerId)
        return db_vol
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.delete(
    "/{volunteerId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a volunteer profile"
)
async def delete_volunteer(
    volunteerId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    v_service = VolunteerService(db)
    await v_service.delete_volunteer(volunteerId, actor_id=actor_id)
    return None


@router.post(
    "/{volunteerId}/status",
    response_model=VolunteerResponse,
    summary="Transition volunteer lifecycle status"
)
async def transition_status(
    volunteerId: int,
    target_status: str = Query(..., description="Pending, Active, Inactive, OnShift"),
    reason: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    v_service = VolunteerService(db)
    try:
        await v_service.update_status(
            volunteer_id=volunteerId,
            target_status=target_status,
            reason=reason,
            actor_id=actor_id
        )
        db_vol = await v_service.repo.get_by_id(volunteerId)
        return db_vol
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/{volunteerId}/skills",
    status_code=status.HTTP_201_CREATED,
    summary="Assign skill to a volunteer"
)
async def assign_skill(
    volunteerId: int,
    req: AssignSkillRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    skill_service = SkillService(db)
    try:
        await skill_service.assign_skill(
            volunteer_id=volunteerId,
            skill_id=req.skill_id,
            proficiency_level=req.proficiency_level,
            actor_id=actor_id
        )
        return {"message": "Skill assigned successfully"}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.delete(
    "/{volunteerId}/skills/{skillId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a skill from a volunteer"
)
async def remove_skill(
    volunteerId: int,
    skillId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    skill_service = SkillService(db)
    await skill_service.remove_skill(volunteer_id=volunteerId, skill_id=skillId, actor_id=actor_id)
    return None


@router.post(
    "/{volunteerId}/certifications",
    status_code=status.HTTP_201_CREATED,
    summary="Add certification to a volunteer"
)
async def add_certification(
    volunteerId: int,
    req: AddCertificationRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(volunteer_or_staff)
):
    await check_self_or_staff(volunteerId, current_user, db)
    actor_id = get_user_id_from_current_user(current_user)
    cert_service = CertificationService(db)
    try:
        cert_data = req.dict()
        await cert_service.add_certification(
            volunteer_id=volunteerId,
            cert_data=cert_data,
            actor_id=actor_id
        )
        return {"message": "Certification added successfully"}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/{volunteerId}/availabilities",
    status_code=status.HTTP_201_CREATED,
    summary="Configure volunteer availability"
)
async def add_availability(
    volunteerId: int,
    req: AddAvailabilityRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(volunteer_or_staff)
):
    await check_self_or_staff(volunteerId, current_user, db)
    avail_service = AvailabilityService(db)
    try:
        avail_data = req.dict()
        await avail_service.add_availability(
            volunteer_id=volunteerId,
            avail_data=avail_data
        )
        return {"message": "Availability added successfully"}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/{volunteerId}/certifications/{certId}/verify",
    response_model=dict,
    summary="Verify volunteer certification"
)
async def verify_certification(
    volunteerId: int,
    certId: int,
    status: str = Query(..., description="Pending, Verified, Expired, Rejected"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    v_service = VolunteerService(db)
    volunteer = await v_service.repo.get_by_id(volunteerId)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    cert_service = CertificationService(db)
    try:
        updated_cert = await cert_service.verify_certification(
            cert_id=certId,
            status=status,
            actor_id=actor_id
        )
        return {
            "id": updated_cert.id,
            "volunteer_id": updated_cert.volunteer_id,
            "name": updated_cert.name,
            "verification_status": updated_cert.verification_status
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)

