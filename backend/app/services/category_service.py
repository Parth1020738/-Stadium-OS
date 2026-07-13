from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from backend.app.repositories.knowledge_repository import KnowledgeCategoryRepository, AuditLogRepository
from backend.app.models.knowledge import KnowledgeCategory, AuditLog
from backend.app.core.logging import logger
from datetime import datetime, timezone
import json

class KnowledgeCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeCategoryRepository(db)
        self.audit_repo = AuditLogRepository(db)

    async def create_category(self, name: str, description: str | None = None, actor_id: int | None = None) -> KnowledgeCategory:
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Category name is required")
        
        existing = await self.repo.get_by_name(name.strip())
        if existing:
            raise HTTPException(status_code=400, detail="Category name already exists")
            
        category = KnowledgeCategory(name=name.strip(), description=description)
        await self.repo.create(category)
        
        # Audit log
        details = {"category_name": category.name, "description": category.description}
        audit_entry = AuditLog(
            action="CREATE_CATEGORY",
            user_id=actor_id,
            details=details,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "CREATE_CATEGORY",
            "actor_id": actor_id,
            "category_id": category.id,
            "category_name": category.name,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return category

    async def get_category(self, category_id: int) -> KnowledgeCategory:
        category = await self.repo.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category

    async def list_categories(self, limit: int = 50, offset: int = 0) -> list[KnowledgeCategory]:
        return await self.repo.list_categories(limit=limit, offset=offset)

    async def update_category(self, category_id: int, name: str, description: str | None = None, actor_id: int | None = None) -> KnowledgeCategory:
        category = await self.get_category(category_id)
        
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Category name is required")
        
        # Check uniqueness if name changed
        if name.strip() != category.name:
            existing = await self.repo.get_by_name(name.strip())
            if existing:
                raise HTTPException(status_code=400, detail="Category name already exists")
                
        category.name = name.strip()
        if description is not None:
            category.description = description
            
        # Audit log
        details = {"category_id": category_id, "category_name": category.name}
        audit_entry = AuditLog(
            action="UPDATE_CATEGORY",
            user_id=actor_id,
            details=details,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "UPDATE_CATEGORY",
            "actor_id": actor_id,
            "category_id": category.id,
            "category_name": category.name,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return category

    async def delete_category(self, category_id: int, actor_id: int | None = None) -> bool:
        category = await self.get_category(category_id)
        await self.repo.delete(category)
        
        # Audit log
        details = {"category_id": category_id, "category_name": category.name}
        audit_entry = AuditLog(
            action="DELETE_CATEGORY",
            user_id=actor_id,
            details=details,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        await self.audit_repo.create(audit_entry)
        await self.db.commit()

        # Structured JSON Log
        logger.info(json.dumps({
            "event": "DELETE_CATEGORY",
            "actor_id": actor_id,
            "category_id": category_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }))

        return True

