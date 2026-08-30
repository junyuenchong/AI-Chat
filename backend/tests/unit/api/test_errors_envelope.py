"""Unit tests for the standard API error JSON envelope.

No database — verifies error message and field text sent to clients.
"""

from app.api.v1.chat.dto.request import ChatRequest
from app.core.exceptions import error_body, field_errors_from_validation
from pydantic import ValidationError

# ────────────────────────────────────────────────────────────
# test_error_body_never_returns_empty_message
# Endpoint: all endpoints (shared error envelope)
# Use: clients always receive a non-empty error code and message.
# ────────────────────────────────────────────────────────────


def test_error_body_never_returns_empty_message():
    body = error_body(code="", message="")
    assert body["error"]["message"] == "An error occurred."
    assert body["error"]["code"] == "APP_ERROR"


# ────────────────────────────────────────────────────────────
# test_field_errors_use_required_message_for_missing
# Endpoint: POST /chat/stream, POST /chat/complete
# Use: missing message field shows "This field is required." to the client.
# ────────────────────────────────────────────────────────────


def test_field_errors_use_required_message_for_missing():
    try:
        ChatRequest.model_validate({})
    except ValidationError as exc:
        fields = field_errors_from_validation(exc)
        assert any(f["message"] == "This field is required." for f in fields)
