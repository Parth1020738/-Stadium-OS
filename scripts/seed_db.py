import os
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.core.config import settings
from backend.app.models.auth import Base, User, Role
from backend.app.core.security import hash_password

async def main():
    print("Seeding database...")
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("sqlite://"):
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create Roles
        operator_role = Role(name="Operator", description="Operations center operator")
        admin_role = Role(name="Administrator", description="System administrator")
        steward_role = Role(name="Steward", description="Steward staff member")
        
        session.add_all([operator_role, admin_role, steward_role])
        await session.flush()

        # Create Operator User
        hashed = hash_password("password")
        user = User(
            email="operator@aegis.com",
            hashed_password=hashed,
            is_verified=True,
            is_deleted=False
        )
        user.roles.append(operator_role)
        user.roles.append(admin_role)
        session.add(user)

        await session.commit()
        print("Database seeded successfully with Operator: operator@aegis.com / password")

if __name__ == "__main__":
    asyncio.run(main())
