"""
Auth API routes.

JWT-only authentication for Q2 demo (no Redis sessions).

Request path:
  main.py → api/v1/router.py
    → api/v1/auth/router.py  (this file)
    → application/auth/service.py
"""

from app.api.v1.auth.dto.request import LoginRequest, RegisterRequest
from app.api.v1.auth.dto.response import TokenResponse, UserResponse
from app.application.auth.mapper import AuthMapper
from app.application.auth.service import AuthService
from app.core.dependencies import get_auth_service, get_current_user
from app.infrastructure.database.models import User
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/auth", tags=["auth"])


# ────────────────────────────────────────────────────────
# register
# Path: api/v1/auth/router.py
# Endpoint: POST /auth/register
# Use: create account and return JWT + user profile.
# ────────────────────────────────────────────────────────
@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account."""
    # Step 1 — map HTTP body to User row.
    user = AuthMapper.register_request_to_user(payload)
    # Step 2 — persist and issue JWT.
    user = await auth_service.register_user(user)
    return AuthMapper.user_to_token_response(user)


# ────────────────────────────────────────────────────────
# login
# Path: api/v1/auth/router.py
# Endpoint: POST /auth/login
# Use: verify credentials and return JWT + user profile.
# ────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate with email and password."""
    email, password = AuthMapper.login_credentials(payload)
    user = await auth_service.login_user(email, password)
    return AuthMapper.user_to_token_response(user)


# ────────────────────────────────────────────────────────
# logout
# Path: api/v1/auth/router.py
# Endpoint: POST /auth/logout
# Use: no-op — client discards JWT (stateless auth).
# ────────────────────────────────────────────────────────
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """Stateless JWT — client discards the token."""
    return None


# ────────────────────────────────────────────────────────
# me
# Path: api/v1/auth/router.py
# Endpoint: GET /auth/me
# Use: return the authenticated user's profile from JWT.
# ────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return AuthMapper.user_to_profile_response(user)
