from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.volunteer_schemas import (
    CreateShiftRequest, ShiftResponse, AssignShiftRequest,
    AssignmentResponse, CheckInRequest, CheckOutRequest,
    PaginationResponse, AttendanceResponse, ErrorResponse
)
from backend.app.services.volunteer_service import (
    ShiftService, AssignmentService, AttendanceService, VolunteerService
)
from backend.app.repositories.volunteer_repository import AssignmentRepository
from backend.app.services.validators import ValidationError

router = APIRouter(prefix="/shifts", tags=["Shifts"])

staff_or_admin = RoleChecker(["Staff", "Admin"])
volunteer_or_staff = RoleChecker(["Volunteer", "Staff", "Admin"])

def get_user_id_from_current_user(current_user: dict) -> int:
    sub = current_user.get("sub")
    if sub and str(sub).isdigit():
        return int(sub)
    u_id = current_user.get("user_id")
    if u_id:
        return int(u_id)
    if sub:
        try:
            return int(sub)
        except ValueError:
            return 99999
    raise HTTPException(status_code=401, detail="Invalid token payload: user_id or sub not found")

async def check_assignment_access(assignment_id: int, current_user: dict, db: AsyncSession):
    user_roles = current_user.get("roles", [])
    if any(role in ["Staff", "Admin"] for role in user_roles):
        return True

    user_id = get_user_id_from_current_user(current_user)
    v_service = VolunteerService(db)
    assign_repo = AssignmentRepository(db)
    assignment = await assign_repo.get_assignment_by_id(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    volunteer = await v_service.repo.get_by_id(assignment.volunteer_id)
    if not volunteer or volunteer.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only perform this action for your own assignments"
        )
    return True


@router.post(
    "",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new volunteer shift"
)
async def create_shift(
    req: CreateShiftRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    shift_service = ShiftService(db)
    try:
        shift = await shift_service.create_shift(
            name=req.name,
            start_time=req.start_time,
            end_time=req.end_time,
            location_zone=req.location_zone,
            required_skills=req.required_skills,
            description=req.description,
            actor_id=actor_id
        )
        return shift
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.get(
    "",
    response_model=PaginationResponse,
    summary="List all shifts"
)
async def list_shifts(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    location_zone: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(volunteer_or_staff)
):
    shift_service = ShiftService(db)
    results, total = await shift_service.repo.list_shifts(
        limit=limit,
        offset=offset,
        status=status,
        location_zone=location_zone
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": results
    }


@router.post(
    "/{shiftId}/assign",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a volunteer to a shift"
)
async def assign_shift(
    shiftId: int,
    req: AssignShiftRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    assign_service = AssignmentService(db)
    try:
        assignment = await assign_service.assign_shift(
            shift_id=shiftId,
            volunteer_id=req.volunteer_id,
            actor_id=actor_id
        )
        db_assign = await assign_service.repo.get_assignment_by_id(assignment.id)
        return db_assign
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/assignments/{assignmentId}/reassign",
    response_model=AssignmentResponse,
    summary="Reassign a shift to another volunteer"
)
async def reassign_shift(
    assignmentId: int,
    req: AssignShiftRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(staff_or_admin)
):
    actor_id = get_user_id_from_current_user(current_user)
    assign_service = AssignmentService(db)
    try:
        assignment = await assign_service.reassign_shift(
            assignment_id=assignmentId,
            new_volunteer_id=req.volunteer_id,
            actor_id=actor_id
        )
        db_assign = await assign_service.repo.get_assignment_by_id(assignmentId)
        return db_assign
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/assignments/{assignmentId}/check-in",
    response_model=AttendanceResponse,
    summary="Log volunteer check-in"
)
async def check_in(
    assignmentId: int,
    req: CheckInRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(volunteer_or_staff)
):
    await check_assignment_access(assignmentId, current_user, db)
    actor_id = get_user_id_from_current_user(current_user)
    attend_service = AttendanceService(db)
    try:
        await attend_service.check_in(
            assignment_id=assignmentId,
            verified_by_id=actor_id,
            latitude=req.latitude,
            longitude=req.longitude,
            notes=req.notes,
            actor_id=actor_id
        )
        attendance = await attend_service.repo.get_attendance_by_assignment(assignmentId)
        return attendance
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)


@router.post(
    "/assignments/{assignmentId}/check-out",
    response_model=AttendanceResponse,
    summary="Log volunteer check-out"
)
async def check_out(
    assignmentId: int,
    req: CheckOutRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(volunteer_or_staff)
):
    await check_assignment_access(assignmentId, current_user, db)
    actor_id = get_user_id_from_current_user(current_user)
    attend_service = AttendanceService(db)
    try:
        await attend_service.check_out(
            assignment_id=assignmentId,
            verified_by_id=actor_id,
            latitude=req.latitude,
            longitude=req.longitude,
            notes=req.notes,
            actor_id=actor_id
        )
        attendance = await attend_service.repo.get_attendance_by_assignment(assignmentId)
        return attendance
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)
