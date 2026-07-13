import sys
from pathlib import Path

# Add project root path to sys.path to resolve shared packages locally
root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))

from fastapi import FastAPI
from backend.app.core.config import settings
from backend.app.core.logging import json_logging_middleware
from backend.app.api.v1.endpoints.health import router as health_router
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.users import router as users_router
from backend.app.api.v1.endpoints.documents import router as documents_router
from backend.app.api.v1.endpoints.categories import router as categories_router
from backend.app.api.v1.endpoints.tags import router as tags_router
from backend.app.api.v1.endpoints.crowd_zones import router as crowd_zones_router
from backend.app.api.v1.endpoints.cameras import router as cameras_router
from backend.app.api.v1.endpoints.crowd_telemetry import router as crowd_telemetry_router
from backend.app.api.v1.endpoints.incidents import router as incidents_router
from backend.app.api.v1.endpoints.volunteers import router as volunteers_router
from backend.app.api.v1.endpoints.shifts import router as shifts_router
from backend.app.api.v1.endpoints.transit import router as transit_router
from backend.app.api.v1.endpoints.accessibility import router as accessibility_router
from backend.app.api.v1.endpoints.commands import router as commands_router
from backend.app.api.v1.endpoints.dashboard import router as dashboard_router
from backend.app.api.v1.websocket.dashboard import router as dashboard_ws_router
from backend.app.api.v1.endpoints.ai import router as ai_router


from backend.app.core.redis import redis_manager
from backend.app.core.kafka_producer import kafka_producer

app = FastAPI(
    title="Aegis Smart Stadium OS - Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    import logging
    logger = logging.getLogger("backend.app.main")
    logger.error(f"Database error encountered: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred. Please contact system support."}
    )

app.middleware("http")(json_logging_middleware)

from backend.app.services.aggregation_service import event_aggregator

@app.on_event("startup")
async def startup_event():
    await kafka_producer.start()
    await event_aggregator.start()

@app.on_event("shutdown")
async def shutdown_event():
    await event_aggregator.stop()
    await kafka_producer.stop()
    await redis_manager.close()

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(tags_router, prefix="/api/v1")
app.include_router(crowd_zones_router, prefix="/api/v1/zones", tags=["crowd-zones"])
app.include_router(cameras_router, prefix="/api/v1/cameras", tags=["cameras"])
app.include_router(crowd_telemetry_router, prefix="/api/v1/crowd", tags=["crowd-telemetry"])
app.include_router(incidents_router, prefix="/api/v1/incidents", tags=["incidents"])
app.include_router(volunteers_router, prefix="/api/v1")
app.include_router(shifts_router, prefix="/api/v1")
app.include_router(transit_router, prefix="/api/v1")
app.include_router(accessibility_router, prefix="/api/v1")
app.include_router(commands_router, prefix="/api/v1/commands", tags=["commands"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(dashboard_ws_router)
app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Aegis Smart Stadium OS - FastAPI backend API foundation."}
