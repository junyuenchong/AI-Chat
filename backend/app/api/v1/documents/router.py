"""
Knowledge API routes.

HTTP layer for RAG knowledge-base documents.
Business logic is handled by DocumentsService.
"""

from uuid import UUID

from app.api.v1.documents.dto.request import CreateDocumentRequest
from app.api.v1.documents.dto.response import DocumentResponse
from app.application.documents.mapper import DocumentsMapper
from app.application.documents.service import DocumentsService
from app.core.dependencies import get_current_user, get_documents_service
from app.infrastructure.database.models import User
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/documents", tags=["documents"])


# ────────────────────────────────────────────────────────
# list_documents
# Endpoint: GET /documents
# Lists all uploaded knowledge documents for the current user.
# ────────────────────────────────────────────────────────
@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    user: User = Depends(get_current_user),
    documents_service: DocumentsService = Depends(get_documents_service),
):
    """List all knowledge documents for the authenticated user."""
    rows = await documents_service.list_documents(user)
    return [DocumentsMapper.document_to_response(row) for row in rows]


# ────────────────────────────────────────────────────────
# create_document
# Endpoint: POST /documents
# Uploads text content and queues it for embedding into the knowledge base.
# ────────────────────────────────────────────────────────
@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: CreateDocumentRequest,
    user: User = Depends(get_current_user),
    documents_service: DocumentsService = Depends(get_documents_service),
):
    """Upload a new knowledge document for RAG retrieval."""
    upload = DocumentsMapper.request_to_upload(user.id, payload)
    document = await documents_service.create_document(user, upload)
    return DocumentsMapper.document_to_response(document)


# ────────────────────────────────────────────────────────
# delete_document
# Endpoint: DELETE /documents/{document_id}
# Removes a document and its vector chunks from the knowledge base.
# ────────────────────────────────────────────────────────
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    documents_service: DocumentsService = Depends(get_documents_service),
):
    """Delete a knowledge document and its chunks."""
    await documents_service.delete_document(user, str(document_id))
