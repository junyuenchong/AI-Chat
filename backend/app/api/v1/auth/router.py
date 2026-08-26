"""Auth HTTP routes: register, login, current user profile."""

from fastapi import APIRouter, Depends, status

from app.api.v1.auth.dto import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.core.dependencies import get_auth_service, get_current_user
from app.models.user import User
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Register — create account; response never includes hashed_password.
# ---------------------------------------------------------------------------
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.register(payload)


# ---------------------------------------------------------------------------
# Login — same TokenResponse shape as register for one UI path.
# ---------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.login(payload)


# ---------------------------------------------------------------------------
# Me — JWT required; restore session after page refresh.
# ---------------------------------------------------------------------------
@router.get("/me", response_model=UserResponse)
async def me(
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_profile(user)
