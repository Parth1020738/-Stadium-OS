import pytest
from httpx import AsyncClient, ASGITransport
from ai.app.main import app

@pytest.mark.asyncio
async def test_ai_gateway_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/ai/query", json={"task_type": "complex_reasoning"})
    assert response.status_code == 200
    assert response.json()["routed_model"] == "gemini-1.5-pro"
