from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.config import settings
from app.database import get_session
from app.models.user import User

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(
    user_id: int, expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(days=settings.JWT_EXPIRATION_DAYS)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = session.get(User, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user
