from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.models.auth import User, Role
from backend.app.models.user_domain import UserProfile, UserPreferences

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(
            User.id == user_id, 
            User.is_deleted == False
        ).options(
            selectinload(User.profile),
            selectinload(User.preferences),
            selectinload(User.roles)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(
            User.email == email,
            User.is_deleted == False
        ).options(
            selectinload(User.profile),
            selectinload(User.preferences),
            selectinload(User.roles)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_users(self, limit: int = 50, offset: int = 0, status: str = None) -> list[User]:
        stmt = select(User).where(User.is_deleted == False)
        if status:
            stmt = stmt.where(User.status == status)
        stmt = stmt.offset(offset).limit(limit).options(
            selectinload(User.profile),
            selectinload(User.preferences),
            selectinload(User.roles)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def save(self, user: User):
        await self.db.commit()
