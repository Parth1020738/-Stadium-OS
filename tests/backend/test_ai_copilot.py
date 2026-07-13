import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
import pytest
from backend.app.services.copilot_service import AICopilotService
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_copilot_questions():
    # Instantiation without db connection for simple text heuristics testing
    service = AICopilotService(db=None)

    # EVACUATION PATH QUERY
    res = await service.answer_operator_query("best evacuation path?")
    assert "Gate C" in res["response"]
    assert res["confidence"] > 0.9

    # VOLUNTEERS DEPLOYMENT QUERY
    res = await service.answer_operator_query("recommend volunteer deployment")
    assert "stewards" in res["response"]
    assert res["data"]["deployment"]["stewards_count"] == 3
