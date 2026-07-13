from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from backend.app.repositories.knowledge_repository import KnowledgeTagRepository, AuditLogRepository
from backend.app.models.knowledge import KnowledgeTag, AuditLog
from backend.app.core.logging import logger
from datetime import datetime, timezone
import json

class KnowledgeTagService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeTagRepository(db)
        self.audit_repo = AuditLogRepository(db)

    async def create_tag(self, name: str, actor_id: int | None = None) -> KnowledgeTag:
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Tag name is required")
        
        existing = await self.repo.get_by_name(name.strip())
        if existing:
            raise HTTPException(status_code=400, detail="Tag name already exists")
            
        tag = KnowledgeTag(name=name.strip())
        await self.repo.create(tag)
        
        # Audit log
        details = {"tag_name": tag.name}
        audit_entry = AuditLog(
            action="CREATE_TAG",
            user_id=actor_id,
            details=details,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "CREATE_TAG",
            "actor_id": actor_id,
            "tag_id": tag.id,
            "tag_name": tag.name,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return tag

    async def get_tag(self, tag_id: int) -> KnowledgeTag:
        tag = await self.repo.get_by_id(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        return tag

    async def list_tags(self, limit: int = 50, offset: int = 0) -> list[KnowledgeTag]:
        return await self.repo.list_tags(limit=limit, offset=offset)

    async def update_tag(self, tag_id: int, name: str, actor_id: int | None = None) -> KnowledgeTag:
        tag = await self.get_tag(tag_id)
        
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Tag name is required")
        
        # Check uniqueness if name changed
        if name.strip() != tag.name:
            existing = await self.repo.get_by_name(name.strip())
            if existing:
                raise HTTPException(status_code=400, detail="Tag name already exists")
                
        tag.name = name.strip()
            
        # Audit log
        details = {"tag_id": tag_id, "tag_name": tag.name}
        audit_entry = AuditLog(
            action="UPDATE_TAG",
            user_id=actor_id,
            details=details,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "UPDATE_TAG",
            "actor_id": actor_id,
            "tag_id": tag.id,
            "tag_name": tag.name,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return tag

    async def delete_tag(self, tag_id: int, actor_id: int | None = None) -> bool:
        tag = await self.get_tag(tag_id)
        await self.repo.delete(tag)
        
        # Audit log
        details = {"tag_id": tag_id, "tag_name": tag.name}
        audit_entry = AuditLog(
            action="DELETE_TAG",
            user_id=actor_id,
            details=details,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "DELETE_TAG",
            "actor_id": actor_id,
            "tag_id": tag_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return True

