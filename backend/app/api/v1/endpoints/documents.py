from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.knowledge import (
    KnowledgeDocumentOut,
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
    KnowledgeDocumentSearchResponse,
    KnowledgeVersionOut,
    KnowledgeAttachmentOut,
    KnowledgeAttachmentCreate,
    get_document_dto,
    get_version_dto,
    get_attachment_dto
)
from backend.app.services.document_service import KnowledgeDocumentService
from backend.app.services.attachment_service import KnowledgeAttachmentService

router = APIRouter(prefix="/documents", tags=["Documents"])

class CategoryAssignRequest(BaseModel):
    category_id: int

class TagAssignRequest(BaseModel):
    tag_ids: List[int]

@router.post("/", response_model=KnowledgeDocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(
    req: KnowledgeDocumentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    actor_id = current_user.get("user_id")
    doc = await srv.create_document(
        title=req.title,
        content=req.content,
        metadata_json=req.metadata_json,
        category_ids=req.category_ids,
        tag_ids=req.tag_ids,
        actor_id=actor_id
    )
    return get_document_dto(doc)

@router.get("/search", response_model=KnowledgeDocumentSearchResponse)
async def search_documents_endpoint(
    title: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    status: Optional[str] = None,
    owner_id: Optional[int] = None,
    created_start: Optional[datetime] = None,
    created_end: Optional[datetime] = None,
    updated_start: Optional[datetime] = None,
    updated_end: Optional[datetime] = None,
    published_start: Optional[datetime] = None,
    published_end: Optional[datetime] = None,
    archived_start: Optional[datetime] = None,
    archived_end: Optional[datetime] = None,
    version_number: Optional[int] = None,
    sort_by: str = "id",
    sort_dir: str = "asc",
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    items, total = await srv.search_documents(
        title=title,
        category=category,
        tags=tags,
        status=status,
        owner_id=owner_id,
        created_start=created_start,
        created_end=created_end,
        updated_start=updated_start,
        updated_end=updated_end,
        published_start=published_start,
        published_end=published_end,
        archived_start=archived_start,
        archived_end=archived_end,
        version_number=version_number,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset
    )
    return KnowledgeDocumentSearchResponse(
        items=[get_document_dto(doc) for doc in items],
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/", response_model=List[KnowledgeDocumentOut])
async def list_documents(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    # Simple list redirects to search
    srv = KnowledgeDocumentService(db)
    items, _ = await srv.search_documents(limit=limit, offset=offset)
    return [get_document_dto(doc) for doc in items]

@router.get("/{documentId}", response_model=KnowledgeDocumentOut)
async def get_document(
    documentId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    doc = await srv.get_document(documentId)
    return get_document_dto(doc)

@router.put("/{documentId}", response_model=KnowledgeDocumentOut)
async def update_document(
    documentId: int,
    req: KnowledgeDocumentUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    actor_id = current_user.get("user_id")
    doc = await srv.update_document(
        document_id=documentId,
        title=req.title,
        content=req.content,
        version_id=req.version_id,
        metadata_json=req.metadata_json,
        actor_id=actor_id
    )
    return get_document_dto(doc)

@router.delete("/{documentId}", response_model=KnowledgeDocumentOut)
async def soft_delete_document(
    documentId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    actor_id = current_user.get("user_id")
    doc = await srv.soft_delete_document(documentId, actor_id=actor_id)
    return get_document_dto(doc)

@router.post("/{documentId}/publish", response_model=KnowledgeDocumentOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def publish_document(
    documentId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    actor_id = current_user.get("user_id")
    doc = await srv.publish_document(documentId, actor_id=actor_id)
    return get_document_dto(doc)

@router.post("/{documentId}/archive", response_model=KnowledgeDocumentOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def archive_document(
    documentId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    actor_id = current_user.get("user_id")
    doc = await srv.archive_document(documentId, actor_id=actor_id)
    return get_document_dto(doc)

@router.post("/{documentId}/restore", response_model=KnowledgeDocumentOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def restore_document(
    documentId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    actor_id = current_user.get("user_id")
    doc = await srv.restore_document(documentId, actor_id=actor_id)
    return get_document_dto(doc)

@router.get("/{documentId}/versions", response_model=List[KnowledgeVersionOut])
async def get_document_versions(
    documentId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    doc = await srv.get_document(documentId)
    return [get_version_dto(v) for v in doc.versions]

@router.post("/{documentId}/categories", response_model=KnowledgeDocumentOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def assign_category(
    documentId: int,
    req: CategoryAssignRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    actor_id = current_user.get("user_id")
    doc = await srv.assign_category(documentId, req.category_id, actor_id=actor_id)
    return get_document_dto(doc)

@router.delete("/{documentId}/categories/{categoryId}", response_model=KnowledgeDocumentOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def remove_category(
    documentId: int,
    categoryId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    actor_id = current_user.get("user_id")
    doc = await srv.remove_category(documentId, categoryId, actor_id=actor_id)
    return get_document_dto(doc)

@router.post("/{documentId}/tags", response_model=KnowledgeDocumentOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def assign_tags(
    documentId: int,
    req: TagAssignRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    actor_id = current_user.get("user_id")
    doc = await srv.assign_tags(documentId, req.tag_ids, actor_id=actor_id)
    return get_document_dto(doc)

@router.delete("/{documentId}/tags/{tagId}", response_model=KnowledgeDocumentOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def remove_tag(
    documentId: int,
    tagId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeDocumentService(db)
    actor_id = current_user.get("user_id")
    doc = await srv.remove_tags(documentId, [tagId], actor_id=actor_id)
    return get_document_dto(doc)

@router.post("/{documentId}/attachments", response_model=KnowledgeAttachmentOut)
async def register_attachment(
    documentId: int,
    req: KnowledgeAttachmentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeAttachmentService(db)
    actor_id = current_user.get("user_id")
    attach = await srv.register_attachment(
        document_id=documentId,
        filename=req.filename,
        mime_type=req.mime_type,
        checksum_sha256=req.checksum_sha256,
        content_length=req.content_length,
        storage_provider=req.storage_provider,
        storage_uri=req.storage_uri,
        virus_scan_status=req.virus_scan_status,
        actor_id=actor_id
    )
    return get_attachment_dto(attach)

@router.get("/{documentId}/attachments/{attachmentId}", response_model=KnowledgeAttachmentOut)
async def get_attachment(
    documentId: int,
    attachmentId: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeAttachmentService(db)
    attach = await srv.get_attachment(attachmentId)
    if attach.document_id != documentId:
        raise HTTPException(status_code=400, detail="Attachment is associated with a different document")
    return get_attachment_dto(attach)
