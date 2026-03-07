"""
Auth API Routes — Authentication
=================================
FastAPI endpoints for user registration and login.
Currently generates stub JWT tokens in memory; will use bcrypt + python-jose
in production.
"""

from fastapi import APIRouter, HTTPException

from ..schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
)
from ...services import auth_service

router = APIRouter(tags=["Authentication"])


# ──────────────────────────────────────────────
# REGISTER — Create new user
# ──────────────────────────────────────────────


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user",
)
def register(body: RegisterRequest):
    """
    Register a new user and return a JWT access token.

    Flow:
      1. Validate email is not already registered
      2. Hash the password (TODO: bcrypt)
      3. Persist in `users` table (TODO: PostgreSQL)
      4. Generate a JWT access token (TODO: python-jose)

    Responses:
      - 201: User created → TokenResponse
      - 409: Email already registered
    """
    result = auth_service.register_user(
        email=body.email,
        password=body.password,
        name=body.name,
    )
    if result is None:
        raise HTTPException(
            status_code=409,
            detail=f"Email '{body.email}' is already registered",
        )
    return result


# ──────────────────────────────────────────────
# LOGIN — Authenticate user
# ──────────────────────────────────────────────


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
)
def login(body: LoginRequest):
    """
    Authenticate a user with email and password.

    Flow:
      1. Look up user by email
      2. Verify password (TODO: bcrypt.checkpw)
      3. Generate a JWT access token (TODO: python-jose)

    Responses:
      - 200: Authentication successful → TokenResponse
      - 401: Invalid credentials
    """
    result = auth_service.login_user(
        email=body.email,
        password=body.password,
    )
    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )
    return result
