"""
Knowledge API routes.

HTTP layer for RAG knowledge-base documents.
Business logic is handled by KnowledgeService.
"""

from uuid import UUID

from app.api.v1.knowledge.dto.request import CreateDocumentRequest
from app.api.v1.knowledge.dto.response import DocumentResponse
from app.application.knowledge.service import KnowledgeService
from app.core.dependencies import get_current_user, get_knowledge_service
from app.infrastructure.database.models.user import User
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/documents", tags=["knowledge"])


# ────────────────────────────────────────────────────────
# list_documents
# Endpoint: GET /documents
# Lists all uploaded knowledge documents for the current user.
# ────────────────────────────────────────────────────────
@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    user: User = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    """List all knowledge documents for the authenticated user."""
    # Return document metadata for the knowledge-base page.
    return await knowledge_service.list_documents(user)


# ────────────────────────────────────────────────────────
# create_document
# Endpoint: POST /documents
# Uploads text content and queues it for embedding into the knowledge base.
# ────────────────────────────────────────────────────────
@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: CreateDocumentRequest,
    user: User = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    """Upload a new knowledge document for RAG retrieval."""
    # Persist the document and queue background embedding into the vector store.
    return await knowledge_service.create_document(user, payload)


# ────────────────────────────────────────────────────────
# delete_document
# Endpoint: DELETE /documents/{document_id}
# Removes a document and its vector chunks from the knowledge base.
# ────────────────────────────────────────────────────────
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    """Delete a knowledge document and its chunks."""
    # Remove the document record and its associated vector chunks.
    await knowledge_service.delete_document(user, str(document_id))
