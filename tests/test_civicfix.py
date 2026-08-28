import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.agents.civicfix_agent import civicfix_agent
from app.agents.adk_agent import adk_civic_agent
from app.agents import tools
from app.services.firestore import firestore_service
from app.services.gemini import gemini_service
from app.models.case import CaseStatus, PriorityLevel, IssueCategory, VerificationResult, VerificationDecision


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
async def test_adk_agent_initialization():
    adk_def = adk_civic_agent.get_adk_definition()
    assert adk_def["name"] == "civicfix_root_agent"
    assert "Google ADK" in adk_def["framework"]


@pytest.mark.asyncio
async def test_missing_evidence_cannot_resolve():
    unverified = await gemini_service.verify_resolution_evidence(
        original_problem="Broken streetlight on 4th Ave",
        claim_description="Contractor claims job done",
        evidence_description=""
    )
    assert unverified.verified is False
    assert unverified.action == VerificationDecision.REQUEST_EVIDENCE
    assert unverified.confidence_score == 0.0


@pytest.mark.asyncio
async def test_close_case_tool_strictly_blocks_unverified_closure():
    case = await tools.create_case_tool(
        raw_description="Pothole on Main St",
        location="Main St",
        category=IssueCategory.ROADS,
        priority=PriorityLevel.HIGH,
        responsible_department="Roads Department"
    )
    blocked_case = await tools.close_case_tool(case.id, "Premature closure attempt")
    assert blocked_case.status != CaseStatus.RESOLVED
    assert blocked_case.status == CaseStatus.AWAITING_EVIDENCE


@pytest.mark.asyncio
async def test_sufficient_evidence_can_resolve_case():
    case = await tools.create_case_tool(
        raw_description="Streetlight defect",
        location="Unity School",
        category=IssueCategory.STREET_LIGHTING,
        priority=PriorityLevel.HIGH,
        responsible_department="Street Lighting Department"
    )
    passed_eval = VerificationResult(
        verified=True,
        confidence_score=0.95,
        reason="Valid photographic proof",
        evidence_quality="SUFFICIENT",
        action=VerificationDecision.RESOLVE_CASE
    )
    await tools.record_verification_tool(case.id, passed_eval)
    closed_case = await tools.close_case_tool(case.id, "Valid resolution verified")
    assert closed_case.status == CaseStatus.RESOLVED


@pytest.mark.asyncio
async def test_all_five_demo_scenarios():
    for scenario in ["streetlight", "drainage", "pothole", "waste", "water_leak"]:
        res = await civicfix_agent.run_scenario_demo(scenario_key=scenario, delay_seconds=0.01)
        assert res["status"] == "SUCCESS"
        case = await firestore_service.get_case(res["case_id"])
        assert case.status in [CaseStatus.RESOLVED, CaseStatus.CLOSED]
