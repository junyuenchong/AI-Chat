"""Unit tests for request validation and error field formatting."""

from app.api.v1.auth.dto.request import LoginRequest, RegisterRequest
from app.api.v1.chat.dto.request import ChatRequest
from app.core.exceptions import field_errors_from_validation
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


def test_missing_login_fields_become_field_errors():
    try:
        LoginRequest.model_validate({})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        names = {item["field"] for item in fields}
        assert "email" in names
        assert "password" in names
        assert any(item["type"] == "missing" for item in fields)


def test_unknown_login_field_is_rejected():
    try:
        LoginRequest.model_validate(
            {"email": "a@b.com", "password": "secret", "extra": True}
        )
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        assert any(
            item["field"] == "extra" and item["type"] == "extra_forbidden"
            for item in fields
        )


def test_register_requires_all_fields():
    try:
        RegisterRequest.model_validate({"email": "a@b.com"})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        names = {item["field"] for item in fields}
        assert "password" in names
        assert "name" in names


def test_blank_chat_message_is_rejected():
    try:
        ChatRequest.model_validate({"message": "   "})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        assert any(item["field"] == "message" for item in fields)


def test_request_validation_error_uses_same_formatter():
    exc = RequestValidationError(
        [{"loc": ("body", "email"), "msg": "Field required", "type": "missing"}]
    )
    fields = field_errors_from_validation(exc)
    assert fields == [
        {"field": "email", "message": "This field is required.", "type": "missing"}
    ]
