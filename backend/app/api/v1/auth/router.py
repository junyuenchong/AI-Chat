"""
Auth API routes.

HTTP layer for registration, login, logout, and profile.
Business logic is handled by AuthService.
"""

from app.api.v1.auth.dto.request import LoginRequest, RegisterRequest
from app.api.v1.auth.dto.response import TokenResponse, UserResponse
from app.application.auth.service import AuthService
from app.core.config import get_settings
from app.core.cookies import clear_session_cookie, read_session_id, set_session_cookie
from app.core.dependencies import get_auth_service, get_current_user
from app.infrastructure.cache.session import create_session, delete_session
from app.infrastructure.database.models.user import User
from fastapi import APIRouter, Depends, Request, Response, status

router = APIRouter(prefix="/auth", tags=["auth"])


# ────────────────────────────────────────────────────────
# _attach_session_cookie
# Internal — called after register and login.
# Creates a server session and sets the HttpOnly cookie on the response.
# ────────────────────────────────────────────────────────
async def _attach_session_cookie(response: Response, user_id: str) -> None:
    """Set an HttpOnly session cookie after successful auth."""
    # Load cookie name, domain, and TTL from application settings.
    settings = get_settings()
    # Persist a server-side session and receive its opaque id.
    session_id = await create_session(user_id)
    if session_id:
        # Attach the session id as an HttpOnly cookie on the outgoing response.
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
    # Delegate account creation; service returns JWT and basic user fields.
    token = await auth_service.register_user(payload)
    # Browser clients rely on the HttpOnly cookie; API clients use the JWT in the body.
    await _attach_session_cookie(response, str(token.user_id))
    # Return token payload for clients that store the JWT locally.
    return token


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
    # Verify credentials and issue a JWT plus user metadata.
    token = await auth_service.login_user(payload)
    # Start a browser session so cookie-based clients stay signed in.
    await _attach_session_cookie(response, str(token.user_id))
    return token


# ────────────────────────────────────────────────────────
# logout
# Endpoint: POST /auth/logout
# Revokes the current session and clears the session cookie.
# ────────────────────────────────────────────────────────
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response):
    """Revoke the current session and clear the session cookie."""
    # Read cookie configuration so we can locate the session id.
    settings = get_settings()
    # Extract the session id from the incoming request cookie, if present.
    session_id = read_session_id(request, settings)
    if session_id:
        # Remove the session record from Redis so the id can no longer be used.
        await delete_session(session_id)
    # Expire the session cookie in the browser regardless of Redis outcome.
    clear_session_cookie(response, settings)


# ────────────────────────────────────────────────────────
# me
# Endpoint: GET /auth/me
# Returns the logged-in user's profile for the app header.
# ────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def me(
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Return the authenticated user's profile."""
    # Map the ORM user to a public profile DTO (no password hash).
    return await auth_service.get_user_profile(user)
