from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import Optional, Tuple
from backend.app.models.incident import Incident

class IncidentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, incident_id: int) -> Optional[Incident]:
        stmt = select(Incident).where(
            Incident.id == incident_id,
            Incident.is_deleted == False
        ).options(
            selectinload(Incident.timeline_entries),
            selectinload(Incident.evidence_entries),
            selectinload(Incident.attachments),
            selectinload(Incident.comments),
            selectinload(Incident.assignments),
            selectinload(Incident.resolutions),
            selectinload(Incident.escalations),
            selectinload(Incident.notifications),
            selectinload(Incident.audits),
            selectinload(Incident.assigned_responders),
            selectinload(Incident.reporter)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_incidents(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str = None,
        priority: str = None,
        severity: str = None,
        category: str = None,
        search: str = None
    ) -> Tuple[list[Incident], int]:
        # Base query for data
        stmt = select(Incident).where(Incident.is_deleted == False)
        
        # Apply filters
        if status:
            stmt = stmt.where(Incident.status == status)
        if priority:
            stmt = stmt.where(Incident.priority == priority)
        if severity:
            stmt = stmt.where(Incident.severity == severity)
        if category:
            stmt = stmt.where(Incident.category == category)
        if search:
            stmt = stmt.where(
                (Incident.title.ilike(f"%{search}%")) |
                (Incident.description.ilike(f"%{search}%"))
            )
        
        # Count query - reuse filters
        count_stmt = select(func.count(Incident.id)).where(Incident.is_deleted == False)
        if status:
            count_stmt = count_stmt.where(Incident.status == status)
        if priority:
            count_stmt = count_stmt.where(Incident.priority == priority)
        if severity:
            count_stmt = count_stmt.where(Incident.severity == severity)
        if category:
            count_stmt = count_stmt.where(Incident.category == category)
        if search:
            count_stmt = count_stmt.where(
                (Incident.title.ilike(f"%{search}%")) |
                (Incident.description.ilike(f"%{search}%"))
            )
        
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()
        
        # For list view, load only essential fields - defer relationships
        stmt = stmt.offset(offset).limit(limit).options(
            selectinload(Incident.reporter),
            selectinload(Incident.assigned_responders)
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_statistics(self) -> dict:
        # Single aggregated query instead of 6 separate count queries
        stmt = select(
            func.count(Incident.id).label('total'),
            func.count().filter(Incident.status == 'Open').label('open'),
            func.count().filter(Incident.status == 'Assigned').label('assigned'),
            func.count().filter(Incident.status == 'Resolved').label('resolved'),
            func.count().filter(Incident.status == 'Closed').label('closed'),
            func.count().filter(Incident.priority == 'Critical').label('critical')
        ).where(Incident.is_deleted == False)
        
        result = await self.db.execute(stmt)
        row = result.mappings().one()
        
        return {
            "total_incidents": row['total'],
            "open_incidents": row['open'],
            "assigned_incidents": row['assigned'],
            "resolved_incidents": row['resolved'],
            "closed_incidents": row['closed'],
            "critical_priority_count": row['critical']
        }

    async def create(self, incident: Incident) -> Incident:
        self.db.add(incident)
        await self.db.flush()
        return incident

    async def save(self, incident: Incident):
        await self.db.flush()

    async def commit(self):
        await self.db.commit()


class TimelineRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, entry) -> any:
        self.db.add(entry)
        await self.db.flush()
        return entry


class EvidenceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, evidence) -> any:
        self.db.add(evidence)
        await self.db.flush()
        return evidence


class AssignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, assignment) -> any:
        self.db.add(assignment)
        await self.db.flush()
        return assignment


class ResolutionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, resolution) -> any:
        self.db.add(resolution)
        await self.db.flush()
        return resolution


class EscalationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, escalation) -> any:
        self.db.add(escalation)
        await self.db.flush()
        return escalation


class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, comment) -> any:
        self.db.add(comment)
        await self.db.flush()
        return comment


class AttachmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, attachment) -> any:
        self.db.add(attachment)
        await self.db.flush()
        return attachment


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, audit) -> any:
        self.db.add(audit)
        await self.db.flush()
        return audit