"""
routes/auth.py — Registration and login endpoints.

Separated from main.py. Rate-limited via slowapi.
"""

import sqlite3
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
)
from db.connection import get_db

from sqlalchemy.orm import Session
from db.models import User

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


# ── Pydantic Models ───────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters.")
        if len(v) > 50:
            raise ValueError("Username must be at most 50 characters.")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, digits, hyphens, and underscores.")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """Register a new user. Rate limited to 5 attempts/minute per IP."""
    validate_password_strength(user_data.password)

    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email.lower())
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered.",
        )

    hashed = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email.lower(),
        hashed_password=hashed
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log.info(f"[AUTH] New user registered: username='{new_user.username}' id={new_user.id}")
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Authenticate and return a JWT.
    Accepts username OR email in the username field.
    Rate limited to 10 attempts/minute per IP.
    """
    identifier = form_data.username.strip().lower()
    user = db.query(User).filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    # Use constant-time comparison to prevent timing attacks
    if user is None or not verify_password(form_data.password, user.hashed_password):
        log.warning(f"[AUTH] Failed login attempt for identifier='{identifier}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user_id=user.id, username=user.username)
    log.info(f"[AUTH] Login successful: username='{user.username}' id={user.id}")
    return {"access_token": token, "token_type": "bearer"}
