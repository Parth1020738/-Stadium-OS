from fastapi import APIRouter
from ai.app.core.router import model_router

router = APIRouter()

@router.post("/query")
async def execute_agent_query(payload: dict):
    task_type = payload.get("task_type", "general")
    selected = model_router.select_model(task_type)
    
    return {
        "status": "received",
        "routed_model": selected,
        "msg": "Phase 1 AI Gateway mock execution."
    }
