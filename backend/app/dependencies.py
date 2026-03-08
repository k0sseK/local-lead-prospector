import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from . import models

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-secret-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(user: models.User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    hash_slice = user.hashed_password[-10:] if user.hashed_password else ""
    to_encode = {
        "sub": str(user.id),
        "exp": expire,
        "type": "password_reset",
        "hash": hash_slice
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type", "access")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
