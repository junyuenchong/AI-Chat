"""JWT and password hashing tests.

Auth regressions must be caught without standing up Postgres.
"""

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


# ---------------------------------------------------------------------------
# Passwords — store bcrypt hashes only; never compare plaintext in services.
# ---------------------------------------------------------------------------

def test_password_hash_roundtrip():
    hashed = hash_password("demo123")
    assert hashed != "demo123"
    assert verify_password("demo123", hashed)
    assert not verify_password("wrong", hashed)


def test_corrupt_password_hash_is_rejected():
    # Bad stored hash must fail closed (False), not raise into the request path.
    assert not verify_password("demo123", "not-a-bcrypt-hash")


# ---------------------------------------------------------------------------
# JWT — subject is the user id; invalid tokens become UnauthorizedError upstream.
# ---------------------------------------------------------------------------

def test_jwt_roundtrip():
    token = create_access_token("11111111-1111-1111-1111-111111111111")
    assert decode_access_token(token) == "11111111-1111-1111-1111-111111111111"


def test_invalid_token_raises_value_error():
    try:
        decode_access_token("not-a-jwt")
        assert False, "expected ValueError"
    except ValueError:
        pass
