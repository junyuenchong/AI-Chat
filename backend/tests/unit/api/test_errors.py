"""Unit tests for request validation and error field formatting.

No database — tests DTO rules used by auth, chat, and knowledge endpoints.
"""

from app.api.v1.auth.dto.request import LoginRequest, RegisterRequest
from app.api.v1.chat.dto.request import ChatRequest
from app.api.v1.documents.dto.request import CreateDocumentRequest
from app.core.exceptions import field_errors_from_validation
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

# ────────────────────────────────────────────────────────────
# test_missing_login_fields_become_field_errors
# Endpoint: POST /auth/login
# Use: missing email or password returns clear field-level errors.
# ────────────────────────────────────────────────────────────


def test_missing_login_fields_become_field_errors():
    try:
        LoginRequest.model_validate({})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        names = {item["field"] for item in fields}
        assert "email" in names
        assert "password" in names
        assert any(item["type"] == "missing" for item in fields)


# ────────────────────────────────────────────────────────────
# test_unknown_login_field_is_rejected
# Endpoint: POST /auth/login
# Use: extra unknown JSON fields are rejected before login runs.
# ────────────────────────────────────────────────────────────


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


# ────────────────────────────────────────────────────────────
# test_register_requires_all_fields
# Endpoint: POST /auth/register
# Use: sign-up requires email, password, and name — each reported if missing.
# ────────────────────────────────────────────────────────────


def test_register_requires_all_fields():
    try:
        RegisterRequest.model_validate({"email": "a@b.com"})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        names = {item["field"] for item in fields}
        assert "password" in names
        assert "name" in names


# ────────────────────────────────────────────────────────────
# test_blank_chat_message_is_rejected
# Endpoint: POST /chat/stream, POST /chat/complete
# Use: whitespace-only messages are rejected with a message field error.
# ────────────────────────────────────────────────────────────


def test_blank_chat_message_is_rejected():
    try:
        ChatRequest.model_validate({"message": "   "})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        assert any(item["field"] == "message" for item in fields)


# ────────────────────────────────────────────────────────────
# test_blank_document_fields_are_rejected
# Endpoint: POST /documents
# Use: empty filename or content is rejected on upload.
# ────────────────────────────────────────────────────────────


def test_blank_document_fields_are_rejected():
    try:
        CreateDocumentRequest.model_validate({"filename": "  ", "content": "   "})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        names = {item["field"] for item in fields}
        assert "filename" in names
        assert "content" in names


# ────────────────────────────────────────────────────────────
# test_unknown_document_field_is_rejected
# Endpoint: POST /documents
# Use: extra unknown JSON fields are rejected before document save runs.
# ────────────────────────────────────────────────────────────


def test_unknown_document_field_is_rejected():
    try:
        CreateDocumentRequest.model_validate(
            {"filename": "notes.md", "content": "hello", "extra": 1}
        )
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        assert any(
            item["field"] == "extra" and item["type"] == "extra_forbidden"
            for item in fields
        )


# ────────────────────────────────────────────────────────────
# test_request_validation_error_uses_same_formatter
# Endpoint: all POST endpoints (shared error formatter)
# Use: FastAPI validation errors use the same field shape as DTO errors.
# ────────────────────────────────────────────────────────────


def test_request_validation_error_uses_same_formatter():
    exc = RequestValidationError(
        [{"loc": ("body", "email"), "msg": "Field required", "type": "missing"}]
    )
    fields = field_errors_from_validation(exc)
    assert fields == [
        {"field": "email", "message": "This field is required.", "type": "missing"}
    ]
