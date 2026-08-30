"""Unit tests for auth and document mapping helpers."""

from app.infrastructure.database.models import load_models

load_models()

from app.api.v1.auth.dto.request import RegisterRequest
from app.api.v1.documents.dto.request import CreateDocumentRequest
from app.application.auth.mapper import AuthMapper
from app.application.documents.mapper import DocumentsMapper
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


def test_knowledge_mapper_builds_document_entity():
    request = CreateDocumentRequest(
        filename="policy.md", content="Annual leave: 14 days."
    )
    upload = DocumentsMapper.request_to_upload("user-1", request)
    doc = DocumentsMapper.upload_to_document(upload)
    assert doc.user_id == "user-1"
    assert doc.filename == "policy.md"
    assert doc.content == "Annual leave: 14 days."
