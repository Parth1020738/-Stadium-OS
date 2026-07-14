import asyncio
from pathlib import Path
import sys

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

# Add project root to sys.path
root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))

from backend.app.core.config import settings
from backend.app.models.auth import User, Role
from backend.app.core.security import hash_password


OPERATOR_EMAIL = "operator@aegis.com"
OPERATOR_PASSWORD = "password"  # MUST match scripts/seed_db.py


async def repair_user_if_hash_is_invalid(session: AsyncSession, user: User) -> bool:
    """Return True if user was repaired."""
    # We intentionally do not import verify_password() because argon2 can throw multiple exception types.
    # hash validity is determined by doing a verification against the known seed password.
    try:
        # verify_password would require correct plaintext; only operator uses known plaintext here.
        from backend.app.core.security import verify_password

        if user.email == OPERATOR_EMAIL:
            ok = verify_password(user.hashed_password, OPERATOR_PASSWORD)
            if ok:
                return False

            # If stored hash is malformed or doesn't match expected password, repair it.
            user.hashed_password = hash_password(OPERATOR_PASSWORD)
            return True

        # For users other than operator: we do not know plaintext, so we only skip repair.
        return False
    except Exception:
        # Any exception means the stored hash is not usable; repair only for operator.
        if user.email == OPERATOR_EMAIL:
            user.hashed_password = hash_password(OPERATOR_PASSWORD)
            return True
        return False


async def main() -> None:
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("sqlite://"):
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        stmt = select(User).where(User.email == OPERATOR_EMAIL)
        res = await session.execute(stmt)
        operator: User | None = res.scalar_one_or_none()

        if not operator:
            raise RuntimeError(
                f"Operator user {OPERATOR_EMAIL} not found in the target DB. "
                "Run scripts/seed_db.py first, then re-run this repair tool."
            )

        repaired = await repair_user_if_hash_is_invalid(session, operator)
        if repaired:
            await session.commit()
            print(f"[OK] Repaired hashed_password for {OPERATOR_EMAIL} using Argon2.")
        else:
            print(f"[OK] No repair needed for {OPERATOR_EMAIL}; hash verified successfully.")


if __name__ == "__main__":
    asyncio.run(main())

