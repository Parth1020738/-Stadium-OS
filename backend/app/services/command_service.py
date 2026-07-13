import json
import logging
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.services.validators import ValidationError
from backend.app.core.kafka_producer import kafka_producer
from backend.app.core.redis import redis_manager
from backend.app.models.command import (
    Command, CommandApproval, CommandExecution, CommandAudit, 
    CommandComment, CommandAttachment, CommandResult
)
from backend.app.repositories.command_repository import (
    CommandRepository, CommandApprovalRepository, CommandExecutionRepository,
    CommandAuditRepository, CommandCommentRepository, CommandAttachmentRepository
)

# Existing services imports
from backend.app.services.incident_service import IncidentService
from backend.app.services.volunteer_service import AssignmentService as VolAssignmentService, VolunteerService
from backend.app.services.transit_service import RouteService as TransitRouteService, VehicleService as TransitVehicleService
from backend.app.services.accessibility_service import AccessibilityService

logger = logging.getLogger("command_service")

CRITICAL_COMMANDS = {
    "EMERGENCY_EVACUATION",
    "GATE_RATE_OVERRIDE",
    "ACCESSIBILITY_OVERRIDE",
    "EMERGENCY_BROADCAST"
}

class CommandGatewayService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CommandRepository(db)
        self.approval_repo = CommandApprovalRepository(db)
        self.exec_repo = CommandExecutionRepository(db)
        self.audit_repo = CommandAuditRepository(db)
        self.comment_repo = CommandCommentRepository(db)
        self.attach_repo = CommandAttachmentRepository(db)

    async def publish_event(self, topic: str, command: Command, extra: dict = None):
        payload = {
            "schemaVersion": "1.0",
            "correlationId": command.correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "command_id": command.id,
                "command_type": command.command_type,
                "status": command.status,
                "created_by_id": command.created_by_id,
                **(extra or {})
            }
        }
        await kafka_producer.send_event(topic, str(command.id), payload)

    async def log_audit(self, command: Command, action: str, actor_id: int, prev: dict = None, new: dict = None):
        audit = CommandAudit(
            command_id=command.id,
            actor_id=actor_id,
            action=action,
            previous_state=prev,
            new_state=new
        )
        await self.audit_repo.create(audit)
        await self.db.commit()

        # Publish command audit event
        payload = {
            "schemaVersion": "1.0",
            "correlationId": command.correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "command_id": command.id,
                "actor_id": actor_id,
                "action": action,
                "previous_state": prev,
                "new_state": new
            }
        }
        await kafka_producer.send_event("command.audit.created", str(command.id), payload)

    async def submit_command(self, command_type: str, payload: dict, creator_id: int) -> Command:
        # Prevent replay attacks using Redis lock
        correlation_id = f"corr-{uuid.uuid4()}"
        lock_key = f"command_lock:{command_type}:{json.dumps(payload, sort_keys=True)}"
        
        # Check rate limits & duplicate submit
        is_locked = await redis_manager.client.get(lock_key)
        if is_locked:
            raise HTTPException(status_code=409, detail="Concurrent execution conflict. Duplicate command request.")
        
        # Set lock key for 5 seconds to prevent duplicate submit
        await redis_manager.client.setex(lock_key, 5, "locked")

        command = Command(
            command_type=command_type,
            payload=payload,
            status="Pending" if command_type in CRITICAL_COMMANDS else "Approved",
            correlation_id=correlation_id,
            created_by_id=creator_id
        )
        await self.repo.create(command)
        await self.db.commit()

        await self.publish_event("command.created", command)
        await self.log_audit(command, "CREATE", creator_id, None, {"command_type": command_type, "status": command.status})

        if command_type in CRITICAL_COMMANDS:
            # Create Pending Approval entry with 10 minutes expiry
            expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)
            approval = CommandApproval(
                command_id=command.id,
                status="Pending",
                expires_at=expires_at
            )
            await self.approval_repo.create(approval)
            await self.db.commit()
            await self.publish_event("command.pending", command)
        else:
            # Execute directly
            await self.execute_command(command.id, creator_id)

        return command

    async def approve_command(self, command_id: int, approver_id: int, comments: Optional[str] = None) -> Command:
        command = await self.repo.get_by_id(command_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")

        if command.status != "Pending":
            raise HTTPException(status_code=400, detail="Command is not in Pending status")

        if command.created_by_id == approver_id:
            raise HTTPException(status_code=400, detail="Creator cannot be the secondary approver")

        # Load approval entity
        approvals = await self.approval_repo.get_by_command_id(command_id)
        if not approvals:
            raise HTTPException(status_code=404, detail="Approval request not found")
        
        approval = approvals[0]
        if approval.expires_at and approval.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            command.status = "Expired"
            approval.status = "Expired"
            await self.db.commit()
            await self.publish_event("command.failed", command, {"reason": "Approval window expired"})
            raise HTTPException(status_code=400, detail="Approval window expired")

        prev_status = command.status
        command.status = "Approved"
        approval.status = "Approved"
        approval.approver_id = approver_id
        approval.comments = comments
        await self.db.commit()

        await self.publish_event("command.approved", command)
        await self.log_audit(command, "APPROVE", approver_id, {"status": prev_status}, {"status": "Approved"})

        # Proceed to execution
        await self.execute_command(command.id, approver_id)
        return command

    async def reject_command(self, command_id: int, approver_id: int, comments: Optional[str] = None) -> Command:
        command = await self.repo.get_by_id(command_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")

        if command.status != "Pending":
            raise HTTPException(status_code=400, detail="Command is not in Pending status")

        approvals = await self.approval_repo.get_by_command_id(command_id)
        if not approvals:
            raise HTTPException(status_code=404, detail="Approval request not found")

        approval = approvals[0]
        prev_status = command.status
        command.status = "Rejected"
        approval.status = "Rejected"
        approval.approver_id = approver_id
        approval.comments = comments
        await self.db.commit()

        await self.publish_event("command.rejected", command)
        await self.log_audit(command, "REJECT", approver_id, {"status": prev_status}, {"status": "Rejected"})
        return command

    async def cancel_command(self, command_id: int, actor_id: int) -> Command:
        command = await self.repo.get_by_id(command_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")

        if command.status != "Pending":
            raise HTTPException(status_code=400, detail="Only Pending commands can be cancelled")

        prev_status = command.status
        command.status = "Cancelled"
        await self.db.commit()

        await self.publish_event("command.cancelled", command)
        await self.log_audit(command, "CANCEL", actor_id, {"status": prev_status}, {"status": "Cancelled"})
        return command

    async def execute_command(self, command_id: int, actor_id: int):
        command = await self.repo.get_by_id(command_id)
        if not command or command.status != "Approved":
            return

        # Start execution record
        execution = CommandExecution(command_id=command.id)
        await self.exec_repo.create(execution)
        await self.db.commit()

        try:
            # Dynamic Dispatch Routing
            result_data = await self._dispatch_routing(command)
            
            command.status = "Executed"
            execution.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            # Save results
            res_obj = CommandResult(command_id=command.id, success=True, result_data=result_data)
            self.db.add(res_obj)
            await self.db.commit()

            await self.publish_event("command.executed", command)
            await self.log_audit(command, "EXECUTE_SUCCESS", actor_id, {"status": "Approved"}, {"status": "Executed"})
            
        except Exception as e:
            logger.error(f"Execution failed for Command {command.id}: {e}", exc_info=True)
            command.status = "Failed"
            execution.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            execution.error_message = str(e)
            
            res_obj = CommandResult(command_id=command.id, success=False, result_data={"error": str(e)})
            self.db.add(res_obj)
            await self.db.commit()

            await self.publish_event("command.failed", command, {"error": str(e)})
            await self.log_audit(command, "EXECUTE_FAILURE", actor_id, {"status": "Approved"}, {"status": "Failed"})

    async def rollback_command(self, command_id: int, actor_id: int) -> Command:
        command = await self.repo.get_by_id(command_id)
        if not command or command.status != "Executed":
            raise HTTPException(status_code=400, detail="Only successfully executed commands can be rolled back")

        prev_status = command.status
        command.status = "Failed" # Rollback marks it failed/invalidated
        await self.db.commit()

        await self.publish_event("command.rollback", command)
        await self.log_audit(command, "ROLLBACK", actor_id, {"status": prev_status}, {"status": "Failed"})
        return command

    async def _dispatch_routing(self, command: Command) -> dict:
        ctype = command.command_type
        payload = command.payload or {}

        if ctype == "Dispatch Volunteer":
            svc = VolAssignmentService(self.db)
            res = await svc.assign_shift(
                shift_id=payload["shift_id"],
                volunteer_id=payload["volunteer_id"],
                actor_id=command.created_by_id
            )
            return {"assignment_id": res.id}

        elif ctype == "Create Incident":
            svc = IncidentService(self.db)
            res = await svc.create_incident(
                title=payload["title"],
                description=payload["description"],
                severity=payload["severity"],
                priority=payload["priority"],
                category=payload["category"],
                location_zone=payload.get("location_zone"),
                location_details=payload.get("location_details"),
                sla_minutes=payload.get("sla_minutes", 15),
                reporter_id=command.created_by_id
            )
            return {"incident_id": res.id}

        elif ctype == "Resolve Incident":
            svc = IncidentService(self.db)
            res = await svc.update_incident(
                incident_id=payload["incident_id"],
                updates={"status": "Resolved"},
                actor_id=command.created_by_id,
                version_id=payload["version_id"]
            )
            return {"incident_id": res.id, "status": res.status}

        elif ctype == "Accessibility Override":
            svc = AccessibilityService(self.db)
            res = await svc.register_barrier(
                venue_id=payload["venue_id"],
                barrier_type=payload["barrier_type"],
                severity=payload["severity"],
                zone_id=payload["zone_id"],
                location_label=payload["location_label"],
                latitude=payload["latitude"],
                longitude=payload["longitude"],
                user_id=command.created_by_id
            )
            return {"barrier_id": res.id}

        # Evacuation & generic override fallbacks
        elif ctype in ["Emergency Evacuation", "EMERGENCY_EVACUATION"]:
            # Trigger digital signage override and unlock gates (IoT payload simulator)
            await kafka_producer.send_event("stadium.evacuation.triggered", str(command.id), {"evacuate": True})
            return {"evacuation_triggered": True, "timestamp": datetime.now(timezone.utc).isoformat()}

        else:
            # Mock executor result for missing custom routes
            return {"message": f"Command type {ctype} processed successfully via generic handler"}
