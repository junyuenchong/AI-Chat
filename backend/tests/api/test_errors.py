"""DTO validation + error envelope tests (no database).

Guarantees clients get field-level errors, not opaque 500s.
"""

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.v1.auth.dto import LoginRequest, RegisterRequest
from app.api.v1.chat.dto import ChatRequest
from app.api.v1.knowledge.dto import CreateDocumentRequest
from app.core.errors import field_errors_from_validation


# ---------------------------------------------------------------------------
# Auth DTOs — missing / extra fields map into our JSON error shape.
# ---------------------------------------------------------------------------

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
    # extra="forbid" on DTOs — reject unknown keys early.
    try:
        LoginRequest.model_validate({"email": "a@b.com", "password": "secret", "extra": True})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        assert any(item["field"] == "extra" and item["type"] == "extra_forbidden" for item in fields)


def test_register_requires_all_fields():
    try:
        RegisterRequest.model_validate({"email": "a@b.com"})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        names = {item["field"] for item in fields}
        assert "password" in names
        assert "name" in names


# ---------------------------------------------------------------------------
# Chat / Knowledge DTOs — blank strings are invalid, not "empty success".
# ---------------------------------------------------------------------------

def test_blank_chat_message_is_rejected():
    try:
        ChatRequest.model_validate({"message": "   "})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        assert any(item["field"] == "message" for item in fields)


def test_blank_document_fields_are_rejected():
    try:
        CreateDocumentRequest.model_validate({"filename": "  ", "content": "   "})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        names = {item["field"] for item in fields}
        assert "filename" in names
        assert "content" in names


def test_unknown_document_field_is_rejected():
    try:
        CreateDocumentRequest.model_validate(
            {"filename": "notes.md", "content": "hello", "extra": 1}
        )
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        assert any(item["field"] == "extra" and item["type"] == "extra_forbidden" for item in fields)


# ---------------------------------------------------------------------------
# Shared formatter — FastAPI RequestValidationError uses the same field shape.
# ---------------------------------------------------------------------------

def test_request_validation_error_uses_same_formatter():
    exc = RequestValidationError(
        [{"loc": ("body", "email"), "msg": "Field required", "type": "missing"}]
    )
    fields = field_errors_from_validation(exc)
    assert fields == [
        {"field": "email", "message": "This field is required.", "type": "missing"}
    ]
