"""
Security utilities.

Password hashing and JWT token helpers.

Request path:
  application/auth/service.py
    → core/security.py  (this file)
"""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from app.core.config import get_settings
from jwt import InvalidTokenError


# ────────────────────────────────────────────────────────
# hash_password
# Internal — bcrypt password hashing.
# Hashes a plaintext password for storage in the database.
# ────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    # Generate a unique salt and return the hash as a UTF-8 string for storage.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ────────────────────────────────────────────────────────
# verify_password
# Internal — bcrypt password verification.
# Returns False on mismatch or corrupt hash instead of raising.
# ────────────────────────────────────────────────────────
def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its bcrypt hash.

    Corrupt hash must fail closed (False), not raise into the request path.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False  # Treat malformed hashes as a failed login, not a 500.


# ────────────────────────────────────────────────────────
# create_access_token
# Internal — JWT access token creation.
# Encodes user id as subject with configured expiry and secret.
# ────────────────────────────────────────────────────────
def create_access_token(subject: str) -> str:
    """Create a JWT access token; subject is user.id."""
    settings = get_settings()
    # Expiry is anchored to UTC so tokens behave consistently across hosts.
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


# ────────────────────────────────────────────────────────
# decode_access_token
# Internal — JWT access token validation.
# Returns user id from subject; callers map ValueError to HTTP 401.
# ────────────────────────────────────────────────────────
def decode_access_token(token: str) -> str:
    """
    Decode and validate a JWT access token.

    Callers map ValueError → HTTP 401.
    """
    settings = get_settings()
    try:
        # Verify signature, expiry, and algorithm in one step.
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc
    subject = payload.get("sub")
    if not subject:
        raise ValueError("Invalid token")  # Reject tokens missing the user id claim.
    return str(subject)
