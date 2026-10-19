from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import AppError
from app.models import Analysis, User
from app.schemas import ErrorOut, LoginIn, RefreshIn, RegisterIn, TokenPair, UserOut
from app.security.auth import (
    create_token_pair,
    decode_token,
    get_client_id,
    get_current_user,
    hash_password,
    verify_password,
)
from app.security.rate_limit import limit_auth

router = APIRouter(prefix="/auth", tags=["auth"])

ERRORS = {401: {"model": ErrorOut}, 409: {"model": ErrorOut}, 422: {"model": ErrorOut}, 429: {"model": ErrorOut}}

DUMMY_HASH = hash_password("not-a-real-password-used-for-timing")


def claim_anonymous_history(db: Session, user: User, client_id: str | None) -> None:
    if client_id is None:
        return
    db.execute(
        update(Analysis)
        .where(Analysis.user_id.is_(None), Analysis.client_id == client_id)
        .values(user_id=user.id, client_id=None)
    )


@router.post("/register", response_model=TokenPair, status_code=201, responses=ERRORS)
def register(
    payload: RegisterIn,
    request: Request,
    client_id: str | None = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    limit_auth(request)
    email = payload.email.lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise AppError("email_taken", "An account with this email already exists", 409)
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    claim_anonymous_history(db, user, client_id)
    db.commit()
    return create_token_pair(user.id)


@router.post("/login", response_model=TokenPair, responses=ERRORS)
def login(
    payload: LoginIn,
    request: Request,
    client_id: str | None = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    limit_auth(request)
    email = payload.email.lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        verify_password(payload.password, DUMMY_HASH)
        raise AppError("invalid_credentials", "Wrong email or password", 401)
    if not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise AppError("invalid_credentials", "Wrong email or password", 401)
    claim_anonymous_history(db, user, client_id)
    db.commit()
    return create_token_pair(user.id)


@router.post("/refresh", response_model=TokenPair, responses=ERRORS)
def refresh(payload: RefreshIn, db: Session = Depends(get_db)):
    user_id = decode_token(payload.refresh_token, "refresh")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise AppError("invalid_token", "User not found or disabled", 401)
    return create_token_pair(user.id)


@router.get("/me", response_model=UserOut, responses=ERRORS)
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
