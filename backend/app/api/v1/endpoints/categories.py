from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.app.core.dependencies import get_db_session
from backend.app.core.auth_guards import get_current_user, RoleChecker
from backend.app.schemas.knowledge import (
    KnowledgeCategoryOut,
    KnowledgeCategoryCreate,
    KnowledgeCategoryUpdate,
    get_category_dto
)
from backend.app.services.category_service import KnowledgeCategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[KnowledgeCategoryOut])
async def list_categories(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeCategoryService(db)
    cats = await srv.list_categories(limit, offset)
    return [get_category_dto(c) for c in cats]

@router.post("/", response_model=KnowledgeCategoryOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def create_category(
    req: KnowledgeCategoryCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeCategoryService(db)
    actor_id = current_user.get("user_id")
    cat = await srv.create_category(req.name, req.description, actor_id=actor_id)
    return get_category_dto(cat)

@router.put("/{categoryId}", response_model=KnowledgeCategoryOut, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def update_category(
    categoryId: int,
    req: KnowledgeCategoryUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeCategoryService(db)
    actor_id = current_user.get("user_id")
    cat = await srv.update_category(categoryId, req.name, req.description, actor_id=actor_id)
    return get_category_dto(cat)

@router.delete("/{categoryId}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["Admin", "OperationsManager"]))])
async def delete_category(
    categoryId: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    srv = KnowledgeCategoryService(db)
    actor_id = current_user.get("user_id")
    await srv.delete_category(categoryId, actor_id=actor_id)
