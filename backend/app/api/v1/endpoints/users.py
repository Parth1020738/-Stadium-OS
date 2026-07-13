from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from backend.app.core.dependencies import get_db_session
from backend.app.services.user_service import UserService
from backend.app.core.auth_guards import get_current_user, RoleChecker

router = APIRouter(prefix="/users", tags=["Users"])

class UserProfileDTO(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None

class UserPreferencesDTO(BaseModel):
    language: str
    receive_notifications: bool

class UserResponseDTO(BaseModel):
    id: int
    email: str
    status: str
    version_id: int
    profile: Optional[UserProfileDTO] = None
    preferences: Optional[UserPreferencesDTO] = None
    roles: List[str]

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class UpdateUserRequest(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    version_id: int

class RoleRequest(BaseModel):
    role_name: str

def get_user_dto(user) -> UserResponseDTO:
    return UserResponseDTO(
        id=user.id,
        email=user.email,
        status=user.status,
        version_id=user.version_id,
        profile=UserProfileDTO(
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            phone=user.profile.phone
        ) if user.profile else None,
        preferences=UserPreferencesDTO(
            language=user.preferences.language,
            receive_notifications=user.preferences.receive_notifications
        ) if user.preferences else None,
        roles=[r.name for r in user.roles]
    )

@router.post("/", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_user(req: CreateUserRequest, db: AsyncSession = Depends(get_db_session)):
    srv = UserService(db)
    user = await srv.create_user(req.email, req.password, req.first_name, req.last_name)
    return get_user_dto(user)

@router.get("/{userId}", response_model=UserResponseDTO)
async def get_user(userId: int, db: AsyncSession = Depends(get_db_session), current_user: dict = Depends(get_current_user)):
    srv = UserService(db)
    user = await srv.get_user(userId)
    return get_user_dto(user)

@router.put("/{userId}", response_model=UserResponseDTO)
async def update_user(userId: int, req: UpdateUserRequest, db: AsyncSession = Depends(get_db_session), current_user: dict = Depends(get_current_user)):
    srv = UserService(db)
    user = await srv.update_user(userId, req.first_name, req.last_name, req.phone, req.version_id)
    return get_user_dto(user)

@router.delete("/{userId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(userId: int, db: AsyncSession = Depends(get_db_session), current_user: dict = Depends(get_current_user)):
    srv = UserService(db)
    await srv.delete_user(userId)

@router.get("/", response_model=List[UserResponseDTO])
async def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = UserService(db)
    repo = srv.repo
    users = await repo.list_users(limit, offset, status)
    return [get_user_dto(u) for u in users]

@router.post("/{userId}/activate", response_model=UserResponseDTO, dependencies=[Depends(RoleChecker(["Commander"]))])
async def activate_user(userId: int, db: AsyncSession = Depends(get_db_session)):
    srv = UserService(db)
    user = await srv.set_user_status(userId, "Active")
    return get_user_dto(user)

@router.post("/{userId}/deactivate", response_model=UserResponseDTO, dependencies=[Depends(RoleChecker(["Commander"]))])
async def deactivate_user(userId: int, db: AsyncSession = Depends(get_db_session)):
    srv = UserService(db)
    user = await srv.set_user_status(userId, "Deactivated")
    return get_user_dto(user)

@router.post("/{userId}/roles", response_model=UserResponseDTO, dependencies=[Depends(RoleChecker(["Commander"]))])
async def assign_role(userId: int, req: RoleRequest, db: AsyncSession = Depends(get_db_session)):
    srv = UserService(db)
    user = await srv.assign_role(userId, req.role_name)
    return get_user_dto(user)

@router.delete("/{userId}/roles", response_model=UserResponseDTO, dependencies=[Depends(RoleChecker(["Commander"]))])
async def remove_role(userId: int, req: RoleRequest, db: AsyncSession = Depends(get_db_session)):
    srv = UserService(db)
    user = await srv.remove_role(userId, req.role_name)
    return get_user_dto(user)

@router.put("/{userId}/preferences", response_model=UserResponseDTO)
async def update_preferences(userId: int, req: UserPreferencesDTO, db: AsyncSession = Depends(get_db_session), current_user: dict = Depends(get_current_user)):
    srv = UserService(db)
    user = await srv.update_preferences(userId, req.language, req.receive_notifications)
    return get_user_dto(user)
