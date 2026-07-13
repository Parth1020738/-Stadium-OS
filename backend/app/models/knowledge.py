from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.models.auth import Base, User

# Many-to-many relationship mapping document categories
document_categories = Table(
    "document_categories",
    Base.metadata,
    Column("document_id", Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("knowledge_categories.id", ondelete="CASCADE"), primary_key=True)
)

# Many-to-many relationship mapping document tags
document_tags = Table(
    "document_tags",
    Base.metadata,
    Column("document_id", Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("knowledge_tags.id", ondelete="CASCADE"), primary_key=True)
)

class KnowledgeCategory(Base):
    __tablename__ = "knowledge_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)

    documents = relationship("KnowledgeDocument", secondary=document_categories, back_populates="categories")


class KnowledgeTag(Base):
    __tablename__ = "knowledge_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    documents = relationship("KnowledgeDocument", secondary=document_tags, back_populates="tags")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True, nullable=False)
    content = Column(String, nullable=False)
    status = Column(String, default="DRAFT", nullable=False) # DRAFT, REVIEW, APPROVED, PUBLISHED, ARCHIVED, DELETED
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    published_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    version_number = Column(Integer, default=1, nullable=False)
    
    # native optimistic locking version ID
    version_id = Column(Integer, default=1, nullable=False)

    metadata_json = Column("metadata", JSON, nullable=True)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    owner = relationship("User", foreign_keys=[owner_id])
    categories = relationship("KnowledgeCategory", secondary=document_categories, back_populates="documents")
    tags = relationship("KnowledgeTag", secondary=document_tags, back_populates="documents")
    attachments = relationship("KnowledgeAttachment", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("KnowledgeVersion", back_populates="document", cascade="all, delete-orphan")


class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    document = relationship("KnowledgeDocument", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])


class KnowledgeAttachment(Base):
    __tablename__ = "knowledge_attachments"

    attachment_id = Column(String, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    checksum_sha256 = Column(String, nullable=False)
    content_length = Column(Integer, nullable=False)
    storage_provider = Column(String, nullable=False)
    storage_uri = Column(String, nullable=False)
    virus_scan_status = Column(String, nullable=False) # e.g. clean, infected, pending
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    document = relationship("KnowledgeDocument", back_populates="attachments")
    uploader = relationship("User", foreign_keys=[uploaded_by])


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    document_id = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    user = relationship("User", foreign_keys=[user_id])
