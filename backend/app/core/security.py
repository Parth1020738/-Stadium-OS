import jwt
import uuid
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from backend.app.core.config import settings

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(hashed_password: str, password: str) -> bool:
    try:
        return ph.verify(hashed_password, password)
    except VerifyMismatchError:
        return False

def create_access_token(subject: str, roles: list[str]) -> str:
    now_time = datetime.now(timezone.utc)
    expire = now_time + timedelta(minutes=15)
    payload = {
        "sub": subject,
        "roles": roles,
        "exp": expire,
        "iat": now_time,
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def create_refresh_token(subject: str) -> str:
    now_time = datetime.now(timezone.utc)
    expire = now_time + timedelta(days=7)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now_time,
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None
