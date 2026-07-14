from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone

from backend.app.core.dependencies import get_db_session
from backend.app.models.auth import User, Role, RefreshToken
from backend.app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, verify_jwt_token
from backend.app.core.redis import redis_manager
from backend.app.core.auth_guards import get_current_user, RoleChecker

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db_session)):
    # Check if user already exists
    stmt = select(User).where(User.email == req.email)
    res = await db.execute(stmt)
    existing_user = res.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered")

    hashed = hash_password(req.password)
    user = User(email=req.email, hashed_password=hashed, is_verified=False)
    
    # Assign default role 'Steward'
    stmt_role = select(Role).where(Role.name == "Steward")
    res_role = await db.execute(stmt_role)
    steward_role = res_role.scalar_one_or_none()
    if not steward_role:
        steward_role = Role(name="Steward", description="Steward staff role")
        db.add(steward_role)
        await db.flush()
        
    user.roles.append(steward_role)
    db.add(user)
    await db.commit()
    
    return {"message": "User registered successfully"}

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    from sqlalchemy.orm import selectinload
    stmt = select(User).where(User.email == req.email).options(selectinload(User.roles))
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    roles = [r.name for r in user.roles]
    access = create_access_token(str(user.id), roles)
    refresh = create_refresh_token(str(user.id))
    
    # Store refresh token
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    db_refresh = RefreshToken(token=refresh, user_id=user.id, expires_at=expires_at)
    db.add(db_refresh)
    await db.commit()
    
    return {"access_token": access, "refresh_token": refresh}

@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    jti = user.get("jti")
    if not jti:
        raise HTTPException(status_code=400, detail="Missing token identifier")
    # Blacklist token for 15 minutes (access token expiry time)
    await redis_manager.blacklist_token(jti, 900)
    return {"message": "Logged out successfully"}

@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(req: RefreshRequest, db: AsyncSession = Depends(get_db_session)):
    payload = verify_jwt_token(req.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    stmt = select(RefreshToken).where(RefreshToken.token == req.refresh_token, RefreshToken.revoked == False)
    res = await db.execute(stmt)
    db_token = res.scalar_one_or_none()
    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token revoked or missing")
        
    stmt_user = select(User).where(User.id == db_token.user_id)
    res_user = await db.execute(stmt_user)
    user = res_user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    roles = [r.name for r in user.roles]
    new_access = create_access_token(str(user.id), roles)
    new_refresh = create_refresh_token(str(user.id))
    
    # Revoke old refresh token and save new one
    db_token.revoked = True
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    db_new_refresh = RefreshToken(token=new_refresh, user_id=user.id, expires_at=expires_at)
    db.add(db_new_refresh)
    await db.commit()
    
    return {"access_token": new_access, "refresh_token": new_refresh}

@router.post("/verify-email-placeholder")
async def verify_email_placeholder():
    return {"message": "Email verification link has been placeholder-triggered."}

@router.post("/reset-password-placeholder")
async def reset_password_placeholder():
    return {"message": "Password reset flow has been placeholder-triggered."}

# Protected sample route to verify RBAC guards
@router.get("/stewards-only", dependencies=[Depends(RoleChecker(["Steward"]))])
async def stewards_only_route():
    return {"message": "Welcome, Steward!"}
