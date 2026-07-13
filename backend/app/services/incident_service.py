import json
import logging
import re
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError
from fastapi import HTTPException, status

from backend.app.repositories.incident_repository import (
    IncidentRepository, TimelineRepository, EvidenceRepository,
    AssignmentRepository, ResolutionRepository, EscalationRepository,
    CommentRepository, AttachmentRepository, AuditRepository
)
from backend.app.models.incident import (
    Incident, IncidentTimeline, IncidentEvidence, IncidentAttachment,
    IncidentComment, IncidentAssignment, IncidentResolution, IncidentEscalation,
    IncidentAudit
)
from backend.app.models.auth import User
from backend.app.core.kafka_producer import kafka_producer

logger = logging.getLogger("incident_service")

class IncidentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = IncidentRepository(db)
        self.timeline_repo = TimelineRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.assignment_repo = AssignmentRepository(db)
        self.resolution_repo = ResolutionRepository(db)
        self.escalation_repo = EscalationRepository(db)
        self.comment_repo = CommentRepository(db)
        self.attachment_repo = AttachmentRepository(db)
        self.audit_repo = AuditRepository(db)

    async def _log_audit_and_timeline(self, incident_id: int, action: str, description: str, actor_id: int | None, changes: dict = None):
        # Sanitize inputs before logging to prevent log injection
        safe_description = self._sanitize_for_logging(description)
        safe_action = self._sanitize_for_logging(action)
        safe_changes = self._sanitize_dict_for_logging(changes) if changes else None
        
        # 1. Create Timeline Entry
        timeline = IncidentTimeline(
            incident_id=incident_id,
            event_type=action,
            description=description,
            created_by_id=actor_id
        )
        await self.timeline_repo.create(timeline)

        # 2. Create Audit Entry
        audit = IncidentAudit(
            incident_id=incident_id,
            action=action,
            actor_id=actor_id,
            changes_json=json.dumps(safe_changes) if safe_changes else None
        )
        await self.audit_repo.create(audit)
        
        # Log structured JSON with sanitized inputs
        log_payload = {
            "event": f"incident_{safe_action.lower()}",
            "incident_id": incident_id,
            "actor_id": actor_id,
            "description": safe_description,
            "changes": safe_changes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        logger.info(json.dumps(log_payload))

    def _sanitize_for_logging(self, value: str) -> str:
        """Remove control characters to prevent log injection attacks."""
        if not value:
            return value
        # Remove control characters except newlines and tabs
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', str(value))

    def _sanitize_dict_for_logging(self, data: dict) -> dict:
        """Recursively sanitize dictionary values for safe logging."""
        if not data:
            return data
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_dict_for_logging(value)
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_for_logging(value)
            else:
                sanitized[key] = value
        return sanitized

    async def create_incident(self, title: str, description: str, severity: str, priority: str, category: str, location_zone: str | None, location_details: str | None, sla_minutes: int, reporter_id: int) -> Incident:
        sla_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=sla_minutes)
        incident = Incident(
            title=title,
            description=description,
            severity=severity,
            priority=priority,
            category=category,
            status="Open",
            reporter_id=reporter_id,
            location_zone=location_zone,
            location_details=location_details,
            sla_minutes=sla_minutes,
            sla_expires_at=sla_expires_at
        )
        
        await self.repo.create(incident)
        await self.repo.commit()

        await self._log_audit_and_timeline(
            incident_id=incident.id,
            action="CREATE",
            description=f"Incident '{title}' was registered.",
            actor_id=reporter_id
        )
        await self.repo.commit()

        # Publish Kafka Event
        await kafka_producer.send_event(
            topic="incident.created",
            key=str(incident.id),
            value={
                "incident_id": incident.id,
                "title": incident.title,
                "status": incident.status,
                "severity": incident.severity,
                "priority": incident.priority,
                "category": incident.category,
                "reporter_id": reporter_id,
                "sla_expires_at": sla_expires_at.isoformat()
            }
        )

        return incident

    async def update_incident(self, incident_id: int, updates: dict, actor_id: int, version_id: int) -> Incident:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

        if incident.version_id != version_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transaction conflict. Stale data version details.")

        changes = {}
        for key, value in updates.items():
            if value is not None and getattr(incident, key) != value:
                changes[key] = {"old": getattr(incident, key), "new": value}
                setattr(incident, key, value)

        if not changes:
            return incident

        incident.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        try:
            await self.repo.save(incident)
            await self.repo.commit()
        except StaleDataError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transaction conflict. Stale data version details.")

        await self._log_audit_and_timeline(
            incident_id=incident.id,
            action="UPDATE",
            description=f"Incident details updated: {', '.join(changes.keys())}.",
            actor_id=actor_id,
            changes=changes
        )
        await self.repo.commit()

        # Publish Kafka Event
        await kafka_producer.send_event(
            topic="incident.updated",
            key=str(incident.id),
            value={
                "incident_id": incident.id,
                "status": incident.status,
                "changes": changes
            }
        )

        return incident

    async def assign_incident(self, incident_id: int, assigned_user_id: int, actor_id: int) -> Incident:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

        # Assign responder
        user = await self.db.get(User, assigned_user_id)
        if not user or user.is_deleted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user not found")

        # Check if already assigned
        if user in incident.assigned_responders:
            return incident

        incident.assigned_responders.append(user)
        
        is_reassign = len(incident.assigned_responders) > 1
        incident.status = "Assigned"
        incident.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        assignment = IncidentAssignment(
            incident_id=incident_id,
            assigned_user_id=assigned_user_id,
            assigned_by_id=actor_id,
            status="Assigned"
        )
        await self.assignment_repo.create(assignment)
        await self.repo.save(incident)
        await self.repo.commit()

        action_name = "REASSIGN" if is_reassign else "ASSIGN"
        await self._log_audit_and_timeline(
            incident_id=incident.id,
            action=action_name,
            description=f"Incident assigned to user {user.email}.",
            actor_id=actor_id
        )
        await self.repo.commit()

        # Publish Kafka Event
        topic = "incident.reassigned" if is_reassign else "incident.assigned"
        await kafka_producer.send_event(
            topic=topic,
            key=str(incident.id),
            value={
                "incident_id": incident.id,
                "assigned_user_id": assigned_user_id,
                "assigned_by_id": actor_id
            }
        )

        return incident

    async def escalate_incident(self, incident_id: int, escalation_reason: str, actor_id: int) -> Incident:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

        old_status = incident.status
        incident.status = "Escalated"
        incident.priority = "Critical"  # Auto escalate priority
        incident.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        escalation = IncidentEscalation(
            incident_id=incident_id,
            escalated_from_status=old_status,
            escalated_to_status="Escalated",
            escalation_reason=escalation_reason,
            escalated_by_id=actor_id
        )
        await self.escalation_repo.create(escalation)
        await self.repo.save(incident)
        await self.repo.commit()

        await self._log_audit_and_timeline(
            incident_id=incident.id,
            action="ESCALATE",
            description=f"Incident escalated. Reason: {escalation_reason}",
            actor_id=actor_id
        )
        await self.repo.commit()

        # Publish Kafka Event
        await kafka_producer.send_event(
            topic="incident.escalated",
            key=str(incident.id),
            value={
                "incident_id": incident.id,
                "escalated_by": actor_id,
                "reason": escalation_reason
            }
        )

        return incident

    async def resolve_incident(self, incident_id: int, resolution_summary: str, root_cause: str | None, actor_id: int) -> Incident:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

        incident.status = "Resolved"
        incident.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        incident.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        resolution = IncidentResolution(
            incident_id=incident_id,
            resolution_summary=resolution_summary,
            resolved_by_id=actor_id,
            root_cause=root_cause
        )
        await self.resolution_repo.create(resolution)
        await self.repo.save(incident)
        await self.repo.commit()

        await self._log_audit_and_timeline(
            incident_id=incident.id,
            action="RESOLVE",
            description=f"Incident resolved. Summary: {resolution_summary}",
            actor_id=actor_id
        )
        await self.repo.commit()

        # Publish Kafka Event
        await kafka_producer.send_event(
            topic="incident.resolved",
            key=str(incident.id),
            value={
                "incident_id": incident.id,
                "resolved_by": actor_id,
                "resolution_summary": resolution_summary
            }
        )

        return incident

    async def close_incident(self, incident_id: int, actor_id: int) -> Incident:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

        incident.status = "Closed"
        incident.closed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        incident.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        await self.repo.save(incident)
        await self.repo.commit()

        await self._log_audit_and_timeline(
            incident_id=incident.id,
            action="CLOSE",
            description="Incident closed.",
            actor_id=actor_id
        )
        await self.repo.commit()

        # Publish Kafka Event
        await kafka_producer.send_event(
            topic="incident.closed",
            key=str(incident.id),
            value={
                "incident_id": incident.id,
                "closed_by": actor_id
            }
        )

        return incident

    async def reopen_incident(self, incident_id: int, actor_id: int) -> Incident:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

        incident.status = "Open"
        incident.closed_at = None
        incident.resolved_at = None
        incident.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        await self.repo.save(incident)
        await self.repo.commit()

        await self._log_audit_and_timeline(
            incident_id=incident.id,
            action="REOPEN",
            description="Incident reopened.",
            actor_id=actor_id
        )
        await self.repo.commit()

        # Publish Kafka Event
        await kafka_producer.send_event(
            topic="incident.reopened",
            key=str(incident.id),
            value={
                "incident_id": incident.id,
                "reopened_by": actor_id
            }
        )

        return incident

    async def add_comment(self, incident_id: int, comment_text: str, author_id: int) -> IncidentComment:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

        comment = IncidentComment(
            incident_id=incident_id,
            comment_text=comment_text,
            author_id=author_id
        )
        await self.comment_repo.create(comment)
        await self.repo.commit()

        await self._log_audit_and_timeline(
            incident_id=incident_id,
            action="COMMENT_CREATE",
            description=f"Comment added: '{comment_text[:30]}...'",
            actor_id=author_id
        )
        await self.repo.commit()

        # Publish Kafka Event
        await kafka_producer.send_event(
            topic="incident.comment.created",
            key=str(incident_id),
            value={
                "incident_id": incident_id,
                "comment_id": comment.id,
                "author_id": author_id
            }
        )

        return comment

    async def upload_evidence(self, incident_id: int, evidence_type: str, description: str | None, storage_uri: str, checksum_sha256: str | None, uploader_id: int) -> IncidentEvidence:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

        evidence = IncidentEvidence(
            incident_id=incident_id,
            evidence_type=evidence_type,
            description=description,
            storage_uri=storage_uri,
            checksum_sha256=checksum_sha256,
            uploaded_by_id=uploader_id
        )
        await self.evidence_repo.create(evidence)
        await self.repo.commit()

        await self._log_audit_and_timeline(
            incident_id=incident_id,
            action="EVIDENCE_UPLOAD",
            description=f"Evidence metadata uploaded of type {evidence_type}.",
            actor_id=uploader_id
        )
        await self.repo.commit()

        # Publish Kafka Event
        await kafka_producer.send_event(
            topic="incident.evidence.uploaded",
            key=str(incident_id),
            value={
                "incident_id": incident_id,
                "evidence_id": evidence.id,
                "evidence_type": evidence_type,
                "storage_uri": storage_uri
            }
        )

        return evidence

    async def link_attachment(self, incident_id: int, filename: str, file_size: int, mime_type: str, storage_uri: str, uploader_id: int) -> IncidentAttachment:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

        attachment = IncidentAttachment(
            incident_id=incident_id,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            storage_uri=storage_uri,
            uploaded_by_id=uploader_id
        )
        await self.attachment_repo.create(attachment)
        await self.repo.commit()

        await self._log_audit_and_timeline(
            incident_id=incident_id,
            action="ATTACHMENT_LINK",
            description=f"Attachment linked: {filename}.",
            actor_id=uploader_id
        )
        await self.repo.commit()

        return attachment

    async def get_statistics(self) -> dict:
        """Get incident statistics using optimized aggregated query."""
        return await self.repo.get_statistics()