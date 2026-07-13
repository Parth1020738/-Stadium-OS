import sys
from pathlib import Path

# Add workspace root to sys.path to load shared packages
root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))

from fastapi import FastAPI
from ai.app.core.gateway import router as gateway_router

app = FastAPI(
    title="Aegis Smart Stadium OS - AI Gateway Node",
    version="1.0.0"
)

app.include_router(gateway_router, prefix="/api/v1/ai")

@app.get("/")
def read_root():
    return {"status": "AI Platform Node skeleton active."}
