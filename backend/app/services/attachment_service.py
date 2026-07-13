from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from backend.app.repositories.knowledge_repository import KnowledgeAttachmentRepository, KnowledgeDocumentRepository, AuditLogRepository
from backend.app.models.knowledge import KnowledgeAttachment, AuditLog
from backend.app.services.validators import KnowledgeValidator, ValidationError
from backend.app.core.logging import logger
from datetime import datetime, timezone
import json
import uuid

class KnowledgeAttachmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeAttachmentRepository(db)
        self.doc_repo = KnowledgeDocumentRepository(db)
        self.audit_repo = AuditLogRepository(db)

    async def register_attachment(
        self,
        document_id: int,
        filename: str,
        mime_type: str,
        checksum_sha256: str,
        content_length: int,
        storage_provider: str,
        storage_uri: str,
        virus_scan_status: str,
        actor_id: int | None = None
    ) -> KnowledgeAttachment:
        # Check document existence
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Target document not found")

        # Validate attachment metadata
        try:
            KnowledgeValidator.validate_attachment_metadata(
                filename=filename,
                mime_type=mime_type,
                checksum_sha256=checksum_sha256,
                content_length=content_length,
                storage_provider=storage_provider,
                storage_uri=storage_uri,
                virus_scan_status=virus_scan_status
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Validation failed: {e.errors}")

        attachment_id = str(uuid.uuid4())
        attachment = KnowledgeAttachment(
            attachment_id=attachment_id,
            document_id=document_id,
            filename=filename,
            mime_type=mime_type,
            checksum_sha256=checksum_sha256,
            content_length=content_length,
            storage_provider=storage_provider,
            storage_uri=storage_uri,
            virus_scan_status=virus_scan_status,
            uploaded_by=actor_id,
            uploaded_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        await self.repo.create(attachment)

        # Audit logging
        details = {
            "attachment_id": attachment_id,
            "document_id": document_id,
            "filename": filename,
            "storage_provider": storage_provider,
            "storage_uri": storage_uri
        }
        audit_entry = AuditLog(
            action="REGISTER_ATTACHMENT_METADATA",
            document_id=document_id,
            user_id=actor_id,
            details=details,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "REGISTER_ATTACHMENT_METADATA",
            "actor_id": actor_id,
            "document_id": document_id,
            "attachment_id": attachment_id,
            "filename": filename,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return attachment

    async def get_attachment(self, attachment_id: str) -> KnowledgeAttachment:
        attachment = await self.repo.get_by_id(attachment_id)
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment metadata not found")
        return attachment

    async def update_attachment_metadata(
        self,
        attachment_id: str,
        storage_uri: str | None = None,
        virus_scan_status: str | None = None,
        actor_id: int | None = None
    ) -> KnowledgeAttachment:
        attachment = await self.get_attachment(attachment_id)

        old_uri = attachment.storage_uri
        old_status = attachment.virus_scan_status

        if storage_uri is not None:
            attachment.storage_uri = storage_uri
        if virus_scan_status is not None:
            if virus_scan_status not in {"clean", "infected", "pending"}:
                raise HTTPException(status_code=400, detail="Invalid virus scan status")
            attachment.virus_scan_status = virus_scan_status

        # Validate the updated object
        try:
            KnowledgeValidator.validate_attachment_metadata(
                filename=attachment.filename,
                mime_type=attachment.mime_type,
                checksum_sha256=attachment.checksum_sha256,
                content_length=attachment.content_length,
                storage_provider=attachment.storage_provider,
                storage_uri=attachment.storage_uri,
                virus_scan_status=attachment.virus_scan_status
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Validation failed: {e.errors}")

        # Audit logging
        details = {
            "attachment_id": attachment_id,
            "old_storage_uri": old_uri,
            "new_storage_uri": attachment.storage_uri,
            "old_virus_scan_status": old_status,
            "new_virus_scan_status": attachment.virus_scan_status
        }
        audit_entry = AuditLog(
            action="UPDATE_ATTACHMENT_METADATA",
            document_id=attachment.document_id,
            user_id=actor_id,
            details=details,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "UPDATE_ATTACHMENT_METADATA",
            "actor_id": actor_id,
            "document_id": attachment.document_id,
            "attachment_id": attachment_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return attachment
