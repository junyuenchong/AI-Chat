"""Knowledge HTTP routes — AI knowledge base documents (RAG sources)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.knowledge.dto import CreateDocumentRequest, DocumentResponse
from app.core.dependencies import get_current_user
from app.db.document import DocumentRepository
from app.db.session import get_db
from app.models.user import User
from app.services.knowledge import KnowledgeService

router = APIRouter(prefix="/documents", tags=["knowledge"])


def get_knowledge_service(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(DocumentRepository(db))


# ---------------------------------------------------------------------------
# List — metadata only (DTO omits full content).
# ---------------------------------------------------------------------------
@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    user: User = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    return await knowledge_service.list_documents(user)


# ---------------------------------------------------------------------------
# Create — Document → Chunks → enqueue embed job.
# ---------------------------------------------------------------------------
@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: CreateDocumentRequest,
    user: User = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    return await knowledge_service.create_document(user, payload)


# ---------------------------------------------------------------------------
# Delete — removes document and chunks (cascade).
# ---------------------------------------------------------------------------
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    await knowledge_service.delete_document(user, str(document_id))
