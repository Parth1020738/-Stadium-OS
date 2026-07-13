from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from backend.app.models.command import (
    Command, CommandApproval, CommandExecution, CommandAudit, 
    CommandComment, CommandAttachment, CommandResult
)

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def commit(self):
        await self.db.commit()

    async def flush(self):
        await self.db.flush()


class CommandRepository(BaseRepository):
    async def get_by_id(self, command_id: int) -> Optional[Command]:
        stmt = select(Command).where(
            Command.id == command_id,
            Command.is_deleted == False
        ).options(
            selectinload(Command.approvals),
            selectinload(Command.executions),
            selectinload(Command.audits),
            selectinload(Command.comments),
            selectinload(Command.attachments),
            selectinload(Command.results)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, command: Command) -> Command:
        self.db.add(command)
        return command

    async def save(self, command: Command) -> Command:
        # Optimistic locking and refresh handled via session flush/commit
        return command

    async def list_commands(self, limit: int = 50, offset: int = 0, status: str = None) -> List[Command]:
        stmt = select(Command).where(Command.is_deleted == False)
        if status:
            stmt = stmt.where(Command.status == status)
        stmt = stmt.order_by(Command.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class CommandApprovalRepository(BaseRepository):
    async def get_by_id(self, approval_id: int) -> Optional[CommandApproval]:
        stmt = select(CommandApproval).where(
            CommandApproval.id == approval_id,
            CommandApproval.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, approval: CommandApproval) -> CommandApproval:
        self.db.add(approval)
        return approval

    async def get_by_command_id(self, command_id: int) -> List[CommandApproval]:
        stmt = select(CommandApproval).where(
            CommandApproval.command_id == command_id,
            CommandApproval.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class CommandExecutionRepository(BaseRepository):
    async def create(self, execution: CommandExecution) -> CommandExecution:
        self.db.add(execution)
        return execution

    async def get_by_command_id(self, command_id: int) -> List[CommandExecution]:
        stmt = select(CommandExecution).where(
            CommandExecution.command_id == command_id,
            CommandExecution.is_deleted == False
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class CommandAuditRepository(BaseRepository):
    async def create(self, audit: CommandAudit) -> CommandAudit:
        self.db.add(audit)
        return audit

    async def get_by_command_id(self, command_id: int) -> List[CommandAudit]:
        stmt = select(CommandAudit).where(
            CommandAudit.command_id == command_id,
            CommandAudit.is_deleted == False
        ).order_by(CommandAudit.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class CommandCommentRepository(BaseRepository):
    async def create(self, comment: CommandComment) -> CommandComment:
        self.db.add(comment)
        return comment


class CommandAttachmentRepository(BaseRepository):
    async def create(self, attachment: CommandAttachment) -> CommandAttachment:
        self.db.add(attachment)
        return attachment
