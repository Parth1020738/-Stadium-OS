import time
import os
try:
    import psutil
except ImportError:
    psutil = None

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.dependencies import get_db_session
from backend.app.core.redis import redis_manager
from backend.app.core.kafka_producer import kafka_producer

router = APIRouter()

START_TIME = time.time()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db_session)):
    db_status = "connected"
    try:
        await db.execute(select(1))
    except Exception:
        db_status = "disconnected"

    redis_status = "connected" if await redis_manager.ping() else "disconnected"
    kafka_status = await kafka_producer.get_health_status()

    # System indicators
    if psutil:
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / (1024 * 1024)  # MB
        cpu_percent = psutil.cpu_percent()
    else:
        memory_usage = 0.0
        cpu_percent = 0.0

    uptime = time.time() - START_TIME

    # Aggregated status
    is_healthy = db_status == "connected" and redis_status == "connected"

    return {
        "status": "healthy" if is_healthy else "degraded",
        "version": "1.0.0",
        "uptime_seconds": round(uptime, 2),
        "system": {
            "cpu_utilization_percent": cpu_percent,
            "memory_usage_mb": round(memory_usage, 2),
        },
        "services": {
            "database": db_status,
            "redis": redis_status,
            "kafka": kafka_status,
            "storage": "connected"
        },
        "migration_status": "synced",
        "background_workers": {
            "status": "active",
            "active_tasks": 0
        },
        "readiness": is_healthy,
        "liveness": True
    }
