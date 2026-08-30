"""Unit tests for JWT tokens and password hashing.

No database — used by POST /auth/register and POST /auth/login.
"""

import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

# ────────────────────────────────────────────────────────────
# test_password_hash_roundtrip
# Endpoint: POST /auth/register, POST /auth/login (internal)
# Use: passwords are stored hashed and verified correctly on login.
# ────────────────────────────────────────────────────────────


def test_password_hash_roundtrip():
    hashed = hash_password("demo123")
    assert hashed != "demo123"
    assert verify_password("demo123", hashed)
    assert not verify_password("wrong", hashed)


# ────────────────────────────────────────────────────────────
# test_corrupt_password_hash_is_rejected
# Endpoint: POST /auth/login (internal)
# Use: invalid stored hash returns False instead of crashing the request.
# ────────────────────────────────────────────────────────────


def test_corrupt_password_hash_is_rejected():
    assert not verify_password("demo123", "not-a-bcrypt-hash")


# ────────────────────────────────────────────────────────────
# test_jwt_roundtrip
# Endpoint: POST /auth/register, POST /auth/login (internal)
# Use: JWT encodes user id and decodes back to the same subject.
# ────────────────────────────────────────────────────────────


def test_jwt_roundtrip():
    token = create_access_token("11111111-1111-1111-1111-111111111111")
    assert decode_access_token(token) == "11111111-1111-1111-1111-111111111111"


# ────────────────────────────────────────────────────────────
# test_invalid_token_raises_value_error
# Endpoint: GET /auth/me, GET /conversations (internal — auth middleware)
# Use: malformed JWT is rejected before any protected route runs.
# ────────────────────────────────────────────────────────────


def test_invalid_token_raises_value_error():
    with pytest.raises(ValueError):
        decode_access_token("not-a-jwt")
