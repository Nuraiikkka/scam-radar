import re
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import AppError
from app.models import User
from app.settings.conf import settings

password_hasher = PasswordHasher()

CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_token(user_id: int, token_type: str) -> str:
    now = datetime.now(UTC)
    if token_type == "access":
        expires = now + timedelta(minutes=settings.access_token_minutes)
    else:
        expires = now + timedelta(days=settings.refresh_token_days)
    payload = {"sub": str(user_id), "type": token_type, "iat": now, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_token_pair(user_id: int) -> dict:
    return {
        "access_token": create_token(user_id, "access"),
        "refresh_token": create_token(user_id, "refresh"),
        "token_type": "bearer",
        "expires_in": settings.access_token_minutes * 60,
    }


def decode_token(token: str, expected_type: str) -> int:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise AppError("token_expired", "Your session has expired, please log in again", 401)
    except jwt.PyJWTError:
        raise AppError("invalid_token", "The token is not valid", 401)
    if payload.get("type") != expected_type:
        raise AppError("invalid_token", "Wrong token type", 401)
    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        raise AppError("invalid_token", "The token is not valid", 401)


def read_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AppError("invalid_token", "Authorization header must be 'Bearer <token>'", 401)
    return parts[1]


def get_optional_user(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    token = read_bearer_token(authorization)
    if token is None:
        request.state.user_id = None
        return None
    user_id = decode_token(token, "access")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise AppError("invalid_token", "User not found or disabled", 401)
    request.state.user_id = user.id
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise AppError("unauthorized", "Please log in first", 401)
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise AppError("forbidden", "Admin access required", 403)
    return user


def get_client_id(x_client_id: str | None = Header(default=None)) -> str | None:
    if x_client_id is None:
        return None
    if not CLIENT_ID_PATTERN.match(x_client_id):
        raise AppError("invalid_client_id", "X-Client-Id must be 8-64 letters, digits or dashes", 400)
    return x_client_id
