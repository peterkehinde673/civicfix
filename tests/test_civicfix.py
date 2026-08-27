import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.agents.civicfix_agent import civicfix_agent
from app.services.firestore import firestore_service

@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/health")
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_demo():
    res = await civicfix_agent.run_killer_demo_sequence(delay_seconds=0.01)
    assert res["status"] == "SUCCESS"