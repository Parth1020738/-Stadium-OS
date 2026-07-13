from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError
from fastapi import HTTPException
from backend.app.repositories.knowledge_repository import (
    KnowledgeDocumentRepository,
    KnowledgeCategoryRepository,
    KnowledgeTagRepository,
    KnowledgeVersionRepository,
    AuditLogRepository
)
from backend.app.models.knowledge import KnowledgeDocument, KnowledgeVersion, AuditLog
from backend.app.services.validators import KnowledgeValidator, ValidationError
from backend.app.core.logging import logger
from datetime import datetime, timezone
import json

class KnowledgeDocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeDocumentRepository(db)
        self.cat_repo = KnowledgeCategoryRepository(db)
        self.tag_repo = KnowledgeTagRepository(db)
        self.ver_repo = KnowledgeVersionRepository(db)
        self.audit_repo = AuditLogRepository(db)

    async def create_document(
        self,
        title: str,
        content: str,
        metadata_json: dict | None = None,
        category_ids: list[int] | None = None,
        tag_ids: list[int] | None = None,
        actor_id: int | None = None
    ) -> KnowledgeDocument:
        # Validate create fields
        try:
            KnowledgeValidator.validate_document_create(title, content, metadata_json)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Validation failed: {e.errors}")

        # Duplicate Detection
        existing = await self.repo.get_by_title(title.strip())
        if existing:
            raise HTTPException(status_code=400, detail="Document with this title already exists")

        document = KnowledgeDocument(
            title=title.strip(),
            content=content,
            status="DRAFT",
            owner_id=actor_id,
            version_number=1,
            version_id=1,
            metadata_json=metadata_json,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        # Category existence validation and assignment
        if category_ids:
            for cat_id in category_ids:
                cat = await self.cat_repo.get_by_id(cat_id)
                if not cat:
                    raise HTTPException(status_code=400, detail=f"Category with ID {cat_id} does not exist")
                document.categories.append(cat)

        # Tag existence validation and assignment
        if tag_ids:
            for t_id in tag_ids:
                tag = await self.tag_repo.get_by_id(t_id)
                if not tag:
                    raise HTTPException(status_code=400, detail=f"Tag with ID {t_id} does not exist")
                document.tags.append(tag)

        await self.repo.create(document)

        # Create Version 1 record
        initial_ver = KnowledgeVersion(
            document_id=document.id,
            version_number=1,
            title=document.title,
            content=document.content,
            metadata_json=document.metadata_json,
            created_by=actor_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.ver_repo.create(initial_ver)

        # Audit Logging
        details = {
            "document_id": document.id,
            "title": document.title,
            "categories": category_ids,
            "tags": tag_ids
        }
        audit_entry = AuditLog(
            action="CREATE_DOCUMENT",
            document_id=document.id,
            user_id=actor_id,
            details=details,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "CREATE_DOCUMENT",
            "actor_id": actor_id,
            "document_id": document.id,
            "title": document.title,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return await self.repo.get_by_id(document.id)

    async def get_document(self, document_id: int) -> KnowledgeDocument:
        doc = await self.repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    async def update_document(
        self,
        document_id: int,
        title: str,
        content: str,
        version_id: int,
        metadata_json: dict | None = None,
        actor_id: int | None = None
    ) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        # Optimistic Locking Check
        if doc.version_id != version_id:
            raise HTTPException(status_code=409, detail="Transaction conflict. Stale data version details.")

        # Validate input
        try:
            KnowledgeValidator.validate_document_create(title, content, metadata_json)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Validation failed: {e.errors}")

        # Unique title validation
        if title.strip() != doc.title:
            existing = await self.repo.get_by_title(title.strip())
            if existing:
                raise HTTPException(status_code=400, detail="Document with this title already exists")

        # Save fields
        doc.title = title.strip()
        doc.content = content
        if metadata_json is not None:
            doc.metadata_json = metadata_json
        doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        try:
            # Audit logging
            details = {
                "document_id": doc.id,
                "title": doc.title,
                "version_id": version_id
            }
            audit_entry = AuditLog(
                action="UPDATE_DOCUMENT",
                document_id=doc.id,
                user_id=actor_id,
                details=details,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            await self.audit_repo.create(audit_entry)
            await self.db.commit()
        except StaleDataError:
            raise HTTPException(status_code=409, detail="Transaction conflict. Stale data version details.")

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "UPDATE_DOCUMENT",
            "actor_id": actor_id,
            "document_id": doc.id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return await self.repo.get_by_id(doc.id)

    async def soft_delete_document(self, document_id: int, actor_id: int | None = None) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        # Validate transition to DELETED
        try:
            KnowledgeValidator.validate_status_transition(doc.status, "DELETED")
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Lifecycle transition failed: {e.errors}")

        doc.is_deleted = True
        doc.status = "DELETED"
        doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Audit logging
        audit_entry = AuditLog(
            action="SOFT_DELETE_DOCUMENT",
            document_id=doc.id,
            user_id=actor_id,
            details={"document_id": doc.id},
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "SOFT_DELETE_DOCUMENT",
            "actor_id": actor_id,
            "document_id": doc.id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return doc

    async def restore_document(self, document_id: int, actor_id: int | None = None) -> KnowledgeDocument:
        # Bypass repo.get_by_id soft delete filter
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        res = await self.db.execute(stmt)
        doc = res.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Validate transition out of DELETED to DRAFT
        try:
            KnowledgeValidator.validate_status_transition(doc.status, "DRAFT")
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Lifecycle transition failed: {e.errors}")

        doc.is_deleted = False
        doc.status = "DRAFT"
        doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Audit logging
        audit_entry = AuditLog(
            action="RESTORE_DOCUMENT",
            document_id=doc.id,
            user_id=actor_id,
            details={"document_id": doc.id},
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "RESTORE_DOCUMENT",
            "actor_id": actor_id,
            "document_id": doc.id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return await self.repo.get_by_id(doc.id)

    async def archive_document(self, document_id: int, actor_id: int | None = None) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        try:
            KnowledgeValidator.validate_status_transition(doc.status, "ARCHIVED")
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Lifecycle transition failed: {e.errors}")

        doc.status = "ARCHIVED"
        doc.archived_at = datetime.now(timezone.utc).replace(tzinfo=None)
        doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Audit logging
        audit_entry = AuditLog(
            action="ARCHIVE_DOCUMENT",
            document_id=doc.id,
            user_id=actor_id,
            details={"document_id": doc.id},
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "ARCHIVE_DOCUMENT",
            "actor_id": actor_id,
            "document_id": doc.id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return await self.repo.get_by_id(doc.id)

    async def approve_document(self, document_id: int, actor_id: int | None = None) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        try:
            KnowledgeValidator.validate_status_transition(doc.status, "APPROVED")
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Lifecycle transition failed: {e.errors}")

        doc.status = "APPROVED"
        doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Audit logging
        audit_entry = AuditLog(
            action="APPROVE_DOCUMENT",
            document_id=doc.id,
            user_id=actor_id,
            details={"document_id": doc.id},
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "APPROVE_DOCUMENT",
            "actor_id": actor_id,
            "document_id": doc.id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return await self.repo.get_by_id(doc.id)

    async def publish_document(self, document_id: int, actor_id: int | None = None) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        try:
            KnowledgeValidator.validate_status_transition(doc.status, "PUBLISHED")
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Lifecycle transition failed: {e.errors}")

        doc.status = "PUBLISHED"
        doc.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
        doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Audit logging
        audit_entry = AuditLog(
            action="PUBLISH_DOCUMENT",
            document_id=doc.id,
            user_id=actor_id,
            details={"document_id": doc.id},
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "PUBLISH_DOCUMENT",
            "actor_id": actor_id,
            "document_id": doc.id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return await self.repo.get_by_id(doc.id)

    async def submit_for_review(self, document_id: int, actor_id: int | None = None) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        try:
            KnowledgeValidator.validate_status_transition(doc.status, "REVIEW")
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Lifecycle transition failed: {e.errors}")

        doc.status = "REVIEW"
        doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Audit logging
        audit_entry = AuditLog(
            action="SUBMIT_FOR_REVIEW",
            document_id=doc.id,
            user_id=actor_id,
            details={"document_id": doc.id},
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "SUBMIT_FOR_REVIEW",
            "actor_id": actor_id,
            "document_id": doc.id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return await self.repo.get_by_id(doc.id)

    async def create_new_version(
        self,
        document_id: int,
        title: str,
        content: str,
        metadata_json: dict | None = None,
        actor_id: int | None = None
    ) -> KnowledgeVersion:
        doc = await self.get_document(document_id)
        next_ver = doc.version_number + 1

        try:
            KnowledgeValidator.validate_version_sequence(doc.version_number, next_ver)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Validation failed: {e.errors}")

        # Create Version history entry
        version = KnowledgeVersion(
            document_id=document_id,
            version_number=next_ver,
            title=title,
            content=content,
            metadata_json=metadata_json,
            created_by=actor_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.ver_repo.create(version)

        # Update base document properties to match new version
        doc.version_number = next_ver
        doc.title = title.strip()
        doc.content = content
        if metadata_json is not None:
            doc.metadata_json = metadata_json
        doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Audit logging
        audit_entry = AuditLog(
            action="CREATE_VERSION",
            document_id=doc.id,
            user_id=actor_id,
            details={"document_id": doc.id, "new_version": next_ver},
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "CREATE_VERSION",
            "actor_id": actor_id,
            "document_id": doc.id,
            "version_number": next_ver,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return version

    async def rollback_to_version(
        self,
        document_id: int,
        target_version_number: int,
        actor_id: int | None = None
    ) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        target_version = await self.ver_repo.get_by_document_id_and_version(document_id, target_version_number)
        if not target_version:
            raise HTTPException(status_code=404, detail=f"Version {target_version_number} not found for this document")

        # Rollback logic creates a new version history entry preserving linear history
        next_ver = doc.version_number + 1

        new_version_record = KnowledgeVersion(
            document_id=document_id,
            version_number=next_ver,
            title=target_version.title,
            content=target_version.content,
            metadata_json=target_version.metadata_json,
            created_by=actor_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.ver_repo.create(new_version_record)

        # Apply to base document
        doc.version_number = next_ver
        doc.title = target_version.title
        doc.content = target_version.content
        doc.metadata_json = target_version.metadata_json
        doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Audit logging
        audit_entry = AuditLog(
            action="ROLLBACK_VERSION",
            document_id=doc.id,
            user_id=actor_id,
            details={"document_id": doc.id, "target_version": target_version_number, "new_version": next_ver},
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "ROLLBACK_VERSION",
            "actor_id": actor_id,
            "document_id": doc.id,
            "rolled_back_to": target_version_number,
            "new_version": next_ver,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return await self.repo.get_by_id(doc.id)

    async def assign_category(self, document_id: int, category_id: int, actor_id: int | None = None) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        cat = await self.cat_repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

        if cat not in doc.categories:
            doc.categories.append(cat)
            doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

            # Audit logging
            audit_entry = AuditLog(
                action="ASSIGN_CATEGORY",
                document_id=doc.id,
                user_id=actor_id,
                details={"document_id": doc.id, "category_id": category_id},
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            await self.audit_repo.create(audit_entry)
            await self.db.commit()

            # Structured JSON Log
            logger.info(json.dumps({
                "event": "ASSIGN_CATEGORY",
                "actor_id": actor_id,
                "document_id": doc.id,
                "category_id": category_id,
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
            }))

        return await self.repo.get_by_id(doc.id)

    async def remove_category(self, document_id: int, category_id: int, actor_id: int | None = None) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        cat = next((c for c in doc.categories if c.id == category_id), None)
        if not cat:
            raise HTTPException(status_code=400, detail="Category is not assigned to this document")

        doc.categories.remove(cat)
        doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Audit logging
        audit_entry = AuditLog(
            action="REMOVE_CATEGORY",
            document_id=doc.id,
            user_id=actor_id,
            details={"document_id": doc.id, "category_id": category_id},
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "REMOVE_CATEGORY",
            "actor_id": actor_id,
            "document_id": doc.id,
            "category_id": category_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return await self.repo.get_by_id(doc.id)

    async def assign_tags(self, document_id: int, tag_ids: list[int], actor_id: int | None = None) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        added_tags = []
        for tag_id in tag_ids:
            tag = await self.tag_repo.get_by_id(tag_id)
            if not tag:
                raise HTTPException(status_code=400, detail=f"Tag with ID {tag_id} not found")
            if tag not in doc.tags:
                doc.tags.append(tag)
                added_tags.append(tag_id)

        if added_tags:
            doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

            # Audit logging
            audit_entry = AuditLog(
                action="ASSIGN_TAGS",
                document_id=doc.id,
                user_id=actor_id,
                details={"document_id": doc.id, "tag_ids": added_tags},
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            await self.audit_repo.create(audit_entry)
            await self.db.commit()

            # Structured JSON Log
            logger.info(json.dumps({
                "event": "ASSIGN_TAGS",
                "actor_id": actor_id,
                "document_id": doc.id,
                "tag_ids": added_tags,
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
            }))

        return await self.repo.get_by_id(doc.id)

    async def remove_tags(self, document_id: int, tag_ids: list[int], actor_id: int | None = None) -> KnowledgeDocument:
        doc = await self.get_document(document_id)

        removed_tags = []
        for tag_id in tag_ids:
            tag = next((t for t in doc.tags if t.id == tag_id), None)
            if tag:
                doc.tags.remove(tag)
                removed_tags.append(tag_id)

        if removed_tags:
            doc.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

            # Audit logging
            audit_entry = AuditLog(
                action="REMOVE_TAGS",
                document_id=doc.id,
                user_id=actor_id,
                details={"document_id": doc.id, "tag_ids": removed_tags},
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            await self.audit_repo.create(audit_entry)
            await self.db.commit()

            # Structured JSON Log
            logger.info(json.dumps({
                "event": "REMOVE_TAGS",
                "actor_id": actor_id,
                "document_id": doc.id,
                "tag_ids": removed_tags,
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
            }))

        return await self.repo.get_by_id(doc.id)

    async def search_documents(
        self,
        title: str = None,
        category: str = None,
        tags: list[str] = None,
        status: str = None,
        owner_id: int = None,
        created_start = None,
        created_end = None,
        updated_start = None,
        updated_end = None,
        published_start = None,
        published_end = None,
        archived_start = None,
        archived_end = None,
        version_number: int = None,
        sort_by: str = "id",
        sort_dir: str = "asc",
        limit: int = 10,
        offset: int = 0
    ) -> tuple[list[KnowledgeDocument], int]:
        return await self.repo.search_documents(
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
