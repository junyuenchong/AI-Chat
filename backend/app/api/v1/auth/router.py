"""
Auth API routes.

HTTP layer for registration, login, logout, and profile.
Business logic is handled by AuthService.
"""

from app.api.v1.auth.dto.request import LoginRequest, RegisterRequest
from app.api.v1.auth.dto.response import TokenResponse, UserResponse
from app.application.auth.mapper import AuthMapper
from app.application.auth.service import AuthService
from app.core.config import get_settings
from app.core.cookies import clear_session_cookie, read_session_id, set_session_cookie
from app.core.dependencies import get_auth_service, get_current_user
from app.infrastructure.cache.redis import create_session, delete_session
from app.infrastructure.database.models import User
from fastapi import APIRouter, Depends, Request, Response, status

router = APIRouter(prefix="/auth", tags=["auth"])


# ────────────────────────────────────────────────────────
# _attach_session_cookie
# Internal — called after register and login.
# Creates a server session and sets the HttpOnly cookie on the response.
# ────────────────────────────────────────────────────────
async def _attach_session_cookie(response: Response, user_id: str) -> None:
    """Set an HttpOnly session cookie after successful auth."""
    settings = get_settings()
    session_id = await create_session(user_id)
    if session_id:
        set_session_cookie(response, settings, session_id)


# ────────────────────────────────────────────────────────
# register
# Endpoint: POST /auth/register
# Creates a new account and starts a browser session.
# ────────────────────────────────────────────────────────
@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account."""
    user = AuthMapper.register_request_to_user(payload)
    user = await auth_service.register_user(user)
    await _attach_session_cookie(response, str(user.id))
    return AuthMapper.user_to_token_response(user)


# ────────────────────────────────────────────────────────
# login
# Endpoint: POST /auth/login
# Checks email and password, then starts a browser session.
# ────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate with email and password."""
    email, password = AuthMapper.login_credentials(payload)
    user = await auth_service.login_user(email, password)
    await _attach_session_cookie(response, str(user.id))
    return AuthMapper.user_to_token_response(user)


# ────────────────────────────────────────────────────────
# logout
# Endpoint: POST /auth/logout
# Revokes the current session and clears the session cookie.
# ────────────────────────────────────────────────────────
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response):
    """Revoke the current session and clear the session cookie."""
    settings = get_settings()
    session_id = read_session_id(request, settings)
    if session_id:
        await delete_session(session_id)
    clear_session_cookie(response, settings)


# ────────────────────────────────────────────────────────
# me
# Endpoint: GET /auth/me
# Returns the logged-in user's profile for the app header.
# ────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return AuthMapper.user_to_profile_response(user)
