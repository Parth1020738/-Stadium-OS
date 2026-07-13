from sqlalchemy import select, and_, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.knowledge import (
    KnowledgeDocument,
    KnowledgeCategory,
    KnowledgeTag,
    KnowledgeAttachment,
    KnowledgeVersion,
    AuditLog
)

class KnowledgeDocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, document_id: int) -> KnowledgeDocument | None:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.is_deleted == False
        ).options(
            selectinload(KnowledgeDocument.categories),
            selectinload(KnowledgeDocument.tags),
            selectinload(KnowledgeDocument.attachments),
            selectinload(KnowledgeDocument.versions)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_title(self, title: str) -> KnowledgeDocument | None:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.title == title,
            KnowledgeDocument.is_deleted == False
        ).options(
            selectinload(KnowledgeDocument.categories),
            selectinload(KnowledgeDocument.tags)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, document: KnowledgeDocument) -> KnowledgeDocument:
        self.db.add(document)
        await self.db.flush()
        return document

    async def delete(self, document: KnowledgeDocument) -> None:
        await self.db.delete(document)
        await self.db.flush()

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
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.is_deleted == False)

        # Filters
        if title:
            stmt = stmt.where(KnowledgeDocument.title.ilike(f"%{title}%"))
        if category:
            stmt = stmt.join(KnowledgeDocument.categories).where(KnowledgeCategory.name == category)
        if tags:
            # Join tags and filter
            stmt = stmt.join(KnowledgeDocument.tags).where(KnowledgeTag.name.in_(tags))
        if status:
            stmt = stmt.where(KnowledgeDocument.status == status)
        if owner_id is not None:
            stmt = stmt.where(KnowledgeDocument.owner_id == owner_id)
        if created_start:
            stmt = stmt.where(KnowledgeDocument.created_at >= created_start)
        if created_end:
            stmt = stmt.where(KnowledgeDocument.created_at <= created_end)
        if updated_start:
            stmt = stmt.where(KnowledgeDocument.updated_at >= updated_start)
        if updated_end:
            stmt = stmt.where(KnowledgeDocument.updated_at <= updated_end)
        if published_start:
            stmt = stmt.where(KnowledgeDocument.published_at >= published_start)
        if published_end:
            stmt = stmt.where(KnowledgeDocument.published_at <= published_end)
        if archived_start:
            stmt = stmt.where(KnowledgeDocument.archived_at >= archived_start)
        if archived_end:
            stmt = stmt.where(KnowledgeDocument.archived_at <= archived_end)
        if version_number is not None:
            stmt = stmt.where(KnowledgeDocument.version_number == version_number)

        # Distinct check to avoid duplicate rows from joins
        stmt = stmt.distinct()

        # Count Query
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_res = await self.db.execute(count_stmt)
        total_count = count_res.scalar() or 0

        # Sorting
        sort_col = getattr(KnowledgeDocument, sort_by, KnowledgeDocument.id)
        if sort_dir.lower() == "desc":
            stmt = stmt.order_by(desc(sort_col))
        else:
            stmt = stmt.order_by(asc(sort_col))

        # Pagination & Eager Loading
        stmt = stmt.offset(offset).limit(limit).options(
            selectinload(KnowledgeDocument.categories),
            selectinload(KnowledgeDocument.tags),
            selectinload(KnowledgeDocument.attachments),
            selectinload(KnowledgeDocument.versions)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total_count


class KnowledgeCategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: int) -> KnowledgeCategory | None:
        stmt = select(KnowledgeCategory).where(KnowledgeCategory.id == category_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_name(self, name: str) -> KnowledgeCategory | None:
        stmt = select(KnowledgeCategory).where(KnowledgeCategory.name == name)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, category: KnowledgeCategory) -> KnowledgeCategory:
        self.db.add(category)
        await self.db.flush()
        return category

    async def delete(self, category: KnowledgeCategory) -> None:
        await self.db.delete(category)
        await self.db.flush()

    async def list_categories(self, limit: int = 50, offset: int = 0) -> list[KnowledgeCategory]:
        stmt = select(KnowledgeCategory).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class KnowledgeTagRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tag_id: int) -> KnowledgeTag | None:
        stmt = select(KnowledgeTag).where(KnowledgeTag.id == tag_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_name(self, name: str) -> KnowledgeTag | None:
        stmt = select(KnowledgeTag).where(KnowledgeTag.name == name)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, tag: KnowledgeTag) -> KnowledgeTag:
        self.db.add(tag)
        await self.db.flush()
        return tag

    async def delete(self, tag: KnowledgeTag) -> None:
        await self.db.delete(tag)
        await self.db.flush()

    async def list_tags(self, limit: int = 50, offset: int = 0) -> list[KnowledgeTag]:
        stmt = select(KnowledgeTag).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class KnowledgeAttachmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, attachment_id: str) -> KnowledgeAttachment | None:
        stmt = select(KnowledgeAttachment).where(KnowledgeAttachment.attachment_id == attachment_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, attachment: KnowledgeAttachment) -> KnowledgeAttachment:
        self.db.add(attachment)
        await self.db.flush()
        return attachment

    async def delete(self, attachment: KnowledgeAttachment) -> None:
        await self.db.delete(attachment)
        await self.db.flush()


class KnowledgeVersionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_document_id_and_version(self, document_id: int, version_number: int) -> KnowledgeVersion | None:
        stmt = select(KnowledgeVersion).where(
            KnowledgeVersion.document_id == document_id,
            KnowledgeVersion.version_number == version_number
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, version: KnowledgeVersion) -> KnowledgeVersion:
        self.db.add(version)
        await self.db.flush()
        return version


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, entry: AuditLog) -> AuditLog:
        self.db.add(entry)
        await self.db.flush()
        return entry
