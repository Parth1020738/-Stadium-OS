from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.command_schemas import (
    CommandCreate, CommandOut, CommandApprovalAction
)
from backend.app.services.command_service import CommandGatewayService

router = APIRouter()

# Map scopes to roles in Aegis Smart Stadium OS
read_checker = RoleChecker(["Operator", "Administrator", "Steward"])
write_checker = RoleChecker(["Operator", "Administrator"])
approve_checker = RoleChecker(["Administrator", "OperationsManager"])
admin_checker = RoleChecker(["Administrator"])

@router.post("", response_model=CommandOut, status_code=status.HTTP_201_CREATED)
async def create_command(
    req: CommandCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(write_checker)
):
    actor_id = current_user.get("user_id")
    service = CommandGatewayService(db)
    command = await service.submit_command(
        command_type=req.command_type,
        payload=req.payload,
        creator_id=actor_id
    )
    return command

@router.get("", response_model=List[CommandOut])
async def list_commands(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(read_checker)
):
    service = CommandGatewayService(db)
    return await service.repo.list_commands(limit=limit, offset=offset, status=status)

@router.get("/pending", response_model=List[CommandOut])
async def list_pending_commands(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(read_checker)
):
    service = CommandGatewayService(db)
    return await service.repo.list_commands(limit=limit, offset=offset, status="Pending")

@router.get("/history", response_model=List[CommandOut])
async def get_command_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(read_checker)
):
    service = CommandGatewayService(db)
    # Return all non-pending commands as history
    commands = await service.repo.list_commands(limit=limit, offset=offset)
    return [c for c in commands if c.status != "Pending"]

@router.get("/{id}", response_model=CommandOut)
async def get_command_details(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(read_checker)
):
    service = CommandGatewayService(db)
    command = await service.repo.get_by_id(id)
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    return command

@router.post("/{id}/approve", response_model=CommandOut)
async def approve_command(
    id: int,
    action: CommandApprovalAction,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(approve_checker)
):
    actor_id = current_user.get("user_id")
    service = CommandGatewayService(db)
    return await service.approve_command(command_id=id, approver_id=actor_id, comments=action.comments)

@router.post("/{id}/reject", response_model=CommandOut)
async def reject_command(
    id: int,
    action: CommandApprovalAction,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(approve_checker)
):
    actor_id = current_user.get("user_id")
    service = CommandGatewayService(db)
    return await service.reject_command(command_id=id, approver_id=actor_id, comments=action.comments)

@router.post("/{id}/cancel", response_model=CommandOut)
async def cancel_command(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(write_checker)
):
    actor_id = current_user.get("user_id")
    service = CommandGatewayService(db)
    return await service.cancel_command(command_id=id, actor_id=actor_id)

@router.post("/{id}/retry", response_model=CommandOut)
async def retry_command(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(write_checker)
):
    actor_id = current_user.get("user_id")
    service = CommandGatewayService(db)
    command = await service.repo.get_by_id(id)
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    # Reset status and submit again
    new_cmd = await service.submit_command(
        command_type=command.command_type,
        payload=command.payload,
        creator_id=actor_id
    )
    return new_cmd
