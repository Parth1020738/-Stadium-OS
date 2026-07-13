from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.models.auth import Base

class Command(Base):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    command_type = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=True) # JSON payload arguments
    status = Column(String(50), nullable=False, default="Pending") # Pending, Approved, Rejected, Executed, Failed, Cancelled, Expired
    correlation_id = Column(String(255), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    approvals = relationship("CommandApproval", back_populates="command", cascade="all, delete-orphan")
    executions = relationship("CommandExecution", back_populates="command", cascade="all, delete-orphan")
    audits = relationship("CommandAudit", back_populates="command", cascade="all, delete-orphan")
    comments = relationship("CommandComment", back_populates="command", cascade="all, delete-orphan")
    attachments = relationship("CommandAttachment", back_populates="command", cascade="all, delete-orphan")
    results = relationship("CommandResult", back_populates="command", cascade="all, delete-orphan")


class CommandApproval(Base):
    __tablename__ = "command_approvals"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(Integer, ForeignKey("commands.id", ondelete="CASCADE"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, default="Pending") # Pending, Approved, Rejected
    comments = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    command = relationship("Command", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approver_id])


class CommandExecution(Base):
    __tablename__ = "command_executions"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(Integer, ForeignKey("commands.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    command = relationship("Command", back_populates="executions")


class CommandAudit(Base):
    __tablename__ = "command_audits"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(Integer, ForeignKey("commands.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(255), nullable=False)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    command = relationship("Command", back_populates="audits")
    actor = relationship("User", foreign_keys=[actor_id])


class CommandResult(Base):
    __tablename__ = "command_results"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(Integer, ForeignKey("commands.id", ondelete="CASCADE"), nullable=False)
    result_data = Column(JSON, nullable=True)
    success = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    command = relationship("Command", back_populates="results")


class CommandComment(Base):
    __tablename__ = "command_comments"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(Integer, ForeignKey("commands.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    command = relationship("Command", back_populates="comments")
    user = relationship("User", foreign_keys=[user_id])


class CommandAttachment(Base):
    __tablename__ = "command_attachments"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(Integer, ForeignKey("commands.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    command = relationship("Command", back_populates="attachments")
