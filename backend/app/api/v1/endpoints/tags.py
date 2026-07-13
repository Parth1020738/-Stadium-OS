from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.knowledge import (
    KnowledgeTagOut,
    KnowledgeTagCreate,
    KnowledgeTagUpdate,
    get_tag_dto
)
from backend.app.services.tag_service import KnowledgeTagService

router = APIRouter(prefix="/tags", tags=["Tags"])

@router.get("/", response_model=List[KnowledgeTagOut])
async def list_tags(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeTagService(db)
    tags = await srv.list_tags(limit, offset)
    return [get_tag_dto(t) for t in tags]

@router.post("/", response_model=KnowledgeTagOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def create_tag(
    req: KnowledgeTagCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeTagService(db)
    actor_id = current_user.get("user_id")
    tag = await srv.create_tag(req.name, actor_id=actor_id)
    return get_tag_dto(tag)

@router.put("/{tagId}", response_model=KnowledgeTagOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def update_tag(
    tagId: int,
    req: KnowledgeTagUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeTagService(db)
    actor_id = current_user.get("user_id")
    tag = await srv.update_tag(tagId, req.name, actor_id=actor_id)
    return get_tag_dto(tag)

@router.delete("/{tagId}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def delete_tag(
    tagId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeTagService(db)
    actor_id = current_user.get("user_id")
    await srv.delete_tag(tagId, actor_id=actor_id)
