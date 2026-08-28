"""Unit tests for auth and knowledge mappers.

Verifies request-to-entity conversion without hitting HTTP or the database.
"""

from app.infrastructure.database.models import load_models

load_models()

from app.api.v1.auth.dto.request import RegisterRequest
from app.api.v1.knowledge.dto.request import CreateDocumentRequest
from app.application.auth.mapper import AuthMapper
from app.application.knowledge.mapper import KnowledgeMapper
from app.core.security import verify_password

# ────────────────────────────────────────────────────────────
# test_auth_mapper_hashes_password_and_lowercases_email
# Endpoint: POST /auth/register (internal)
# Use: sign-up data is normalized — email lowercased, password hashed.
# ────────────────────────────────────────────────────────────


def test_auth_mapper_hashes_password_and_lowercases_email():
    request = RegisterRequest(email="User@Example.com", password="secret12", name="Ada")
    user = AuthMapper.register_request_to_user(request)
    assert user.email == "user@example.com"
    assert user.hashed_password != "secret12"
    assert verify_password("secret12", user.hashed_password)


# ────────────────────────────────────────────────────────────
# test_auth_token_response_never_includes_hash
# Endpoint: POST /auth/register, POST /auth/login (internal)
# Use: login response includes token and profile — never the password hash.
# ────────────────────────────────────────────────────────────


def test_auth_token_response_never_includes_hash():
    request = RegisterRequest(email="a@b.com", password="secret12", name="Ada")
    user = AuthMapper.register_request_to_user(request)
    token = AuthMapper.user_to_login_response(user)
    assert token.access_token
    assert token.email == "a@b.com"
    assert token.user_id
    assert "hashed_password" not in token.model_dump()


# ────────────────────────────────────────────────────────────
# test_knowledge_mapper_builds_document_entity
# Endpoint: POST /documents (internal)
# Use: upload form fields map to a document row with correct owner and content.
# ────────────────────────────────────────────────────────────


def test_knowledge_mapper_builds_document_entity():
    request = CreateDocumentRequest(
        filename="policy.md", content="Annual leave: 14 days."
    )
    doc = KnowledgeMapper.upload_request_to_document("user-1", request)
    assert doc.user_id == "user-1"
    assert doc.filename == "policy.md"
    assert doc.content == "Annual leave: 14 days."
