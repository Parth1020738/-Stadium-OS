from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.exc import StaleDataError
from fastapi import HTTPException
from datetime import datetime, timezone
from backend.app.repositories.user_repository import UserRepository
from backend.app.models.auth import User, Role
from backend.app.models.user_domain import UserProfile, UserPreferences
from backend.app.core.security import hash_password

class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)
        self.db = db

    async def create_user(self, email: str, password: str, first_name: str, last_name: str) -> User:
        existing = await self.repo.get_by_email(email)
        if existing:
            raise HTTPException(status_code=400, detail="Unique email constraint violation")

        hashed = hash_password(password)
        user = User(email=email, hashed_password=hashed, status="Pending", is_deleted=False)
        profile = UserProfile(first_name=first_name, last_name=last_name)
        prefs = UserPreferences()
        
        user.profile = profile
        user.preferences = prefs

        # Assign default Steward role
        stmt = select(Role).where(Role.name == "Steward")
        res = await self.db.execute(stmt)
        role = res.scalar_one_or_none()
        if not role:
            role = Role(name="Steward", description="Steward staff")
            self.db.add(role)
            await self.db.flush()
        user.roles.append(role)

        await self.repo.create(user)
        await self.repo.save(user)
        return user

    async def get_user(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def update_user(self, user_id: int, first_name: str, last_name: str, phone: str, version_id: int) -> User:
        user = await self.get_user(user_id)
        
        # Concurrency optimistic locking validation check
        if user.version_id != version_id:
            raise HTTPException(status_code=409, detail="Transaction conflict. Stale data version details.")

        user.profile.first_name = first_name
        user.profile.last_name = last_name
        user.profile.phone = phone
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        try:
            await self.repo.save(user)
        except StaleDataError:
            raise HTTPException(status_code=409, detail="Transaction conflict. Stale data version details.")
        return user

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        user.is_deleted = True
        await self.repo.save(user)
        return True

    async def set_user_status(self, user_id: int, status: str) -> User:
        user = await self.get_user(user_id)
        user.status = status
        await self.repo.save(user)
        return user

    async def assign_role(self, user_id: int, role_name: str) -> User:
        user = await self.get_user(user_id)
        
        # Check if already assigned
        if any(r.name == role_name for r in user.roles):
            return user

        stmt = select(Role).where(Role.name == role_name)
        res = await self.db.execute(stmt)
        role = res.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=404, detail="Role target not found")
            
        user.roles.append(role)
        await self.repo.save(user)
        return user

    async def remove_role(self, user_id: int, role_name: str) -> User:
        user = await self.get_user(user_id)
        role_to_remove = next((r for r in user.roles if r.name == role_name), None)
        if not role_to_remove:
            raise HTTPException(status_code=400, detail="User does not have specified role assignment")
            
        user.roles.remove(role_to_remove)
        await self.repo.save(user)
        return user

    async def update_preferences(self, user_id: int, language: str, receive_notifications: bool) -> User:
        user = await self.get_user(user_id)
        user.preferences.language = language
        user.preferences.receive_notifications = receive_notifications
        await self.repo.save(user)
        return user
