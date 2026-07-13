from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from backend.app.repositories.knowledge_repository import KnowledgeVersionRepository, KnowledgeDocumentRepository, AuditLogRepository
from backend.app.models.knowledge import KnowledgeVersion, AuditLog
from backend.app.services.validators import KnowledgeValidator, ValidationError
from backend.app.core.logging import logger
from datetime import datetime, timezone
import json

class KnowledgeVersionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeVersionRepository(db)
        self.doc_repo = KnowledgeDocumentRepository(db)
        self.audit_repo = AuditLogRepository(db)

    async def create_version(
        self,
        document_id: int,
        title: str,
        content: str,
        metadata_json: dict | None = None,
        actor_id: int | None = None
    ) -> KnowledgeVersion:
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        next_ver = doc.version_number + 1

        try:
            KnowledgeValidator.validate_version_sequence(doc.version_number, next_ver)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Validation failed: {e.errors}")

        version = KnowledgeVersion(
            document_id=document_id,
            version_number=next_ver,
            title=title,
            content=content,
            metadata_json=metadata_json,
            created_by=actor_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        await self.repo.create(version)

        # Update document version details
        doc.version_number = next_ver
        
        # Audit logging
        details = {
            "document_id": document_id,
            "version_number": next_ver,
            "title": title
        }
        audit_entry = AuditLog(
            action="CREATE_VERSION",
            document_id=document_id,
            user_id=actor_id,
            details=details,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "CREATE_VERSION",
            "actor_id": actor_id,
            "document_id": document_id,
            "version_number": next_ver,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return version

    async def get_version(self, document_id: int, version_number: int) -> KnowledgeVersion:
        ver = await self.repo.get_by_document_id_and_version(document_id, version_number)
        if not ver:
            raise HTTPException(status_code=404, detail="Version not found")
        return ver
