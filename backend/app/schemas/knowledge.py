from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional, List

class KnowledgeCategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

class KnowledgeCategoryCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None

class KnowledgeCategoryUpdate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class KnowledgeTagOut(BaseModel):
    id: int
    name: str

class KnowledgeTagCreate(BaseModel):
    name: str = Field(..., max_length=255)

class KnowledgeTagUpdate(BaseModel):
    name: str = Field(..., max_length=255)


class KnowledgeAttachmentOut(BaseModel):
    attachment_id: str
    document_id: int
    filename: str
    mime_type: str
    checksum_sha256: str
    content_length: int
    storage_provider: str
    storage_uri: str
    virus_scan_status: str
    uploaded_by: Optional[int] = None
    uploaded_at: datetime

class KnowledgeAttachmentCreate(BaseModel):
    filename: str
    mime_type: str
    checksum_sha256: str = Field(..., min_length=64, max_length=64)
    content_length: int = Field(..., gt=0)
    storage_provider: str
    storage_uri: str
    virus_scan_status: str = Field("pending", pattern="^(clean|infected|pending)$")


class KnowledgeVersionOut(BaseModel):
    id: int
    document_id: int
    version_number: int
    title: str
    content: str
    metadata_json: Optional[dict] = None
    created_at: datetime
    created_by: Optional[int] = None


class KnowledgeDocumentOut(BaseModel):
    id: int
    title: str
    content: str
    status: str
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    version_number: int
    version_id: int
    metadata_json: Optional[dict] = None
    categories: List[KnowledgeCategoryOut] = []
    tags: List[KnowledgeTagOut] = []
    attachments: List[KnowledgeAttachmentOut] = []
    versions: List[KnowledgeVersionOut] = []

class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    metadata_json: Optional[dict] = None
    category_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None

class KnowledgeDocumentUpdate(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    version_id: int
    metadata_json: Optional[dict] = None


class KnowledgeDocumentSearchResponse(BaseModel):
    items: List[KnowledgeDocumentOut]
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    detail: str


# Helper mappers
def get_category_dto(cat) -> KnowledgeCategoryOut:
    return KnowledgeCategoryOut(
        id=cat.id,
        name=cat.name,
        description=cat.description
    )

def get_tag_dto(tag) -> KnowledgeTagOut:
    return KnowledgeTagOut(
        id=tag.id,
        name=tag.name
    )

def get_attachment_dto(attach) -> KnowledgeAttachmentOut:
    return KnowledgeAttachmentOut(
        attachment_id=attach.attachment_id,
        document_id=attach.document_id,
        filename=attach.filename,
        mime_type=attach.mime_type,
        checksum_sha256=attach.checksum_sha256,
        content_length=attach.content_length,
        storage_provider=attach.storage_provider,
        storage_uri=attach.storage_uri,
        virus_scan_status=attach.virus_scan_status,
        uploaded_by=attach.uploaded_by,
        uploaded_at=attach.uploaded_at
    )

def get_version_dto(ver) -> KnowledgeVersionOut:
    return KnowledgeVersionOut(
        id=ver.id,
        document_id=ver.document_id,
        version_number=ver.version_number,
        title=ver.title,
        content=ver.content,
        metadata_json=ver.metadata_json,
        created_at=ver.created_at,
        created_by=ver.created_by
    )

def get_document_dto(doc) -> KnowledgeDocumentOut:
    return KnowledgeDocumentOut(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        status=doc.status,
        owner_id=doc.owner_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        published_at=doc.published_at,
        archived_at=doc.archived_at,
        version_number=doc.version_number,
        version_id=doc.version_id,
        metadata_json=doc.metadata_json,
        categories=[get_category_dto(c) for c in doc.categories] if doc.categories else [],
        tags=[get_tag_dto(t) for t in doc.tags] if doc.tags else [],
        attachments=[get_attachment_dto(a) for a in doc.attachments] if doc.attachments else [],
        versions=[get_version_dto(v) for v in doc.versions] if doc.versions else []
    )
