"""Unit tests for auth mapping helpers."""

from app.infrastructure.database.models import load_models

load_models()

from app.api.v1.auth.dto.request import RegisterRequest
from app.application.auth.mapper import AuthMapper
from app.core.security import verify_password


def test_auth_mapper_hashes_password_and_lowercases_email():
    request = RegisterRequest(email="User@Example.com", password="secret12", name="Ada")
    user = AuthMapper.register_request_to_user(request)
    assert user.email == "user@example.com"
    assert user.hashed_password != "secret12"
    assert verify_password("secret12", user.hashed_password)


def test_auth_token_response_never_includes_hash():
    request = RegisterRequest(email="a@b.com", password="secret12", name="Ada")
    user = AuthMapper.register_request_to_user(request)
    token = AuthMapper.user_to_token_response(user)
    assert token.access_token
    assert token.email == "a@b.com"
    assert token.user_id
    assert "hashed_password" not in token.model_dump()
