from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.incident_schemas import (
    CreateIncidentRequest, UpdateIncidentRequest, AssignIncidentRequest,
    ResolveIncidentRequest, IncidentResponse, TimelineResponse,
    EvidenceResponse, CommentResponse, AttachmentResponse,
    StatisticsResponse, PaginationResponse, ErrorResponse,
    EscalationRequest, CommentRequest, EvidenceRequest, AttachmentRequest
)
from backend.app.services.incident_service import IncidentService
from backend.app.models.incident import IncidentComment, IncidentEvidence, IncidentAttachment

router = APIRouter()

# Scopes / roles check can reuse RoleChecker
steward_or_operator = RoleChecker(["Steward", "Operator", "Administrator"])
operator_or_admin = RoleChecker(["Operator", "Administrator"])

@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new security or medical incident"
)
async def create_incident(
    req: CreateIncidentRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(steward_or_operator)
):
    reporter_id = current_user.get("user_id")
    service = IncidentService(db)
    incident = await service.create_incident(
        title=req.title,
        description=req.description,
        severity=req.severity,
        priority=req.priority,
        category=req.category,
        location_zone=req.location_zone,
        location_details=req.location_details,
        sla_minutes=req.sla_minutes or 15,
        reporter_id=reporter_id
    )
    # Refresh to load relationships
    db_incident = await service.repo.get_by_id(incident.id)
    return db_incident

@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Get incident summary statistics"
)
async def get_statistics(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(steward_or_operator)
):
    service = IncidentService(db)
    stats = await service.get_statistics()
    return stats

@router.get(
    "",
    response_model=PaginationResponse,
    summary="Search, filter, and paginate incidents"
)
async def list_incidents(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(steward_or_operator)
):
    service = IncidentService(db)
    items, total = await service.repo.list_incidents(
        limit=limit,
        offset=offset,
        status=status,
        priority=priority,
        severity=severity,
        category=category,
        search=search
    )
    return PaginationResponse(items=items, total=total, limit=limit, offset=offset)

@router.get(
    "/{id}",
    response_model=IncidentResponse,
    summary="Get detailed incident by ID"
)
async def get_incident(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(steward_or_operator)
):
    service = IncidentService(db)
    incident = await service.repo.get_by_id(id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident

@router.put(
    "/{id}",
    response_model=IncidentResponse,
    summary="Update incident details"
)
async def update_incident(
    id: int,
    req: UpdateIncidentRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(steward_or_operator)
):
    actor_id = current_user.get("user_id")
    service = IncidentService(db)
    updates = req.dict(exclude_unset=True)
    updates.pop("version_id", None)
    
    incident = await service.update_incident(
        incident_id=id,
        updates=updates,
        actor_id=actor_id,
        version_id=req.version_id
    )
    return incident

@router.post(
    "/{id}/assign",
    response_model=IncidentResponse,
    summary="Assign incident to a steward or responder"
)
async def assign_incident(
    id: int,
    req: AssignIncidentRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(operator_or_admin)
):
    actor_id = current_user.get("user_id")
    service = IncidentService(db)
    incident = await service.assign_incident(
        incident_id=id,
        assigned_user_id=req.assigned_user_id,
        actor_id=actor_id
    )
    return incident

@router.post(
    "/{id}/escalate",
    response_model=IncidentResponse,
    summary="Escalate incident severity and priority"
)
async def escalate_incident(
    id: int,
    req: EscalationRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(steward_or_operator)
):
    actor_id = current_user.get("user_id")
    service = IncidentService(db)
    incident = await service.escalate_incident(
        incident_id=id,
        escalation_reason=req.escalation_reason,
        actor_id=actor_id
    )
    return incident

@router.post(
    "/{id}/resolve",
    response_model=IncidentResponse,
    summary="Mark incident as resolved"
)
async def resolve_incident(
    id: int,
    req: ResolveIncidentRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(operator_or_admin)
):
    actor_id = current_user.get("user_id")
    service = IncidentService(db)
    incident = await service.resolve_incident(
        incident_id=id,
        resolution_summary=req.resolution_summary,
        root_cause=req.root_cause,
        actor_id=actor_id
    )
    return incident

@router.post(
    "/{id}/close",
    response_model=IncidentResponse,
    summary="Mark incident as closed"
)
async def close_incident(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(operator_or_admin)
):
    actor_id = current_user.get("user_id")
    service = IncidentService(db)
    incident = await service.close_incident(incident_id=id, actor_id=actor_id)
    return incident

@router.post(
    "/{id}/reopen",
    response_model=IncidentResponse,
    summary="Reopen resolved or closed incident"
)
async def reopen_incident(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(operator_or_admin)
):
    actor_id = current_user.get("user_id")
    service = IncidentService(db)
    incident = await service.reopen_incident(incident_id=id, actor_id=actor_id)
    return incident

@router.post(
    "/{id}/comments",
    response_model=CommentResponse,
    summary="Add operational comment to incident timeline"
)
async def add_comment(
    id: int,
    req: CommentRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(steward_or_operator)
):
    author_id = current_user.get("user_id")
    service = IncidentService(db)
    comment = await service.add_comment(
        incident_id=id,
        comment_text=req.comment_text,
        author_id=author_id
    )
    # Refresh with selectinload to populate relationships
    stmt = select(IncidentComment).where(IncidentComment.id == comment.id).options(selectinload(IncidentComment.author))
    res = await service.db.execute(stmt)
    return res.scalar_one()

@router.post(
    "/{id}/evidence",
    response_model=EvidenceResponse,
    summary="Upload and link evidence metadata"
)
async def upload_evidence(
    id: int,
    req: EvidenceRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(steward_or_operator)
):
    uploader_id = current_user.get("user_id")
    service = IncidentService(db)
    evidence = await service.upload_evidence(
        incident_id=id,
        evidence_type=req.evidence_type,
        description=req.description,
        storage_uri=req.storage_uri,
        checksum_sha256=req.checksum_sha256,
        uploader_id=uploader_id
    )
    # Refresh with selectinload to populate relationships
    stmt = select(IncidentEvidence).where(IncidentEvidence.id == evidence.id).options(selectinload(IncidentEvidence.uploaded_by))
    res = await service.db.execute(stmt)
    return res.scalar_one()

@router.post(
    "/{id}/attachments",
    response_model=AttachmentResponse,
    summary="Link binary attachment files to incident record"
)
async def add_attachment(
    id: int,
    req: AttachmentRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(steward_or_operator)
):
    uploader_id = current_user.get("user_id")
    service = IncidentService(db)
    attachment = await service.link_attachment(
        incident_id=id,
        filename=req.filename,
        file_size=req.file_size,
        mime_type=req.mime_type,
        storage_uri=req.storage_uri,
        uploader_id=uploader_id
    )
    # Refresh with selectinload to populate relationships
    stmt = select(IncidentAttachment).where(IncidentAttachment.id == attachment.id).options(selectinload(IncidentAttachment.uploaded_by))
    res = await service.db.execute(stmt)
    return res.scalar_one()

@router.get(
    "/{id}/timeline",
    response_model=List[TimelineResponse],
    summary="Get full history log and chronological timeline of incident"
)
async def get_timeline(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(steward_or_operator)
):
    from backend.app.models.incident import IncidentTimeline
    service = IncidentService(db)
    incident = await service.repo.get_by_id(id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    # Query timeline entries with eager loading of created_by to avoid MissingGreenlet
    stmt = select(IncidentTimeline).where(
        IncidentTimeline.incident_id == id
    ).options(selectinload(IncidentTimeline.created_by))
    res = await db.execute(stmt)
    return list(res.scalars().all())

