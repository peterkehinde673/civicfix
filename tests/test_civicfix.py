import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.agents.civicfix_agent import civicfix_agent
from app.services.firestore import firestore_service
from app.services.gemini import gemini_service
from app.models.case import CaseStatus, VerificationDecision


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_and_query_case_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/cases", json={
            "description": "Major flood blocking storm drain on Market Road",
            "location": "Market Road Sector 4"
        })
    assert res.status_code == 201
    assert res.json()["id"].startswith("CF-")


@pytest.mark.asyncio
async def test_multimodal_verification_proof_required():
    unverified = await gemini_service.verify_resolution_evidence(
        original_problem="Broken streetlight on 4th Ave",
        claim_description="Contractor reports job done",
        evidence_description=""
    )
    assert unverified.verified is False
    assert unverified.action == VerificationDecision.REQUEST_EVIDENCE


@pytest.mark.asyncio
async def test_multimodal_verification_valid_proof():
    verified = await gemini_service.verify_resolution_evidence(
        original_problem="Broken streetlight on 4th Ave",
        claim_description="Contractor reports job done",
        evidence_description="Photographic proof shows replacement LED fixture illuminated on 4th Ave pole"
    )
    assert verified.verified is True
    assert verified.action == VerificationDecision.RESOLVE_CASE


@pytest.mark.asyncio
async def test_all_5_autonomous_scenarios():
    for scenario in ["streetlight", "drainage", "pothole", "waste", "water_leak"]:
        res = await civicfix_agent.run_scenario_demo(scenario_key=scenario, delay_seconds=0.01)
        assert res["status"] == "SUCCESS"
        case = await firestore_service.get_case(res["case_id"])
        assert case.status in [CaseStatus.RESOLVED, CaseStatus.CLOSED]
