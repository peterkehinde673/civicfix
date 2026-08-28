from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.agents.civicfix_agent import civicfix_agent, DEMO_SCENARIOS

router = APIRouter(prefix="/api/orchestrator", tags=["Autonomous Orchestrator"])


class ProcessReportRequest(BaseModel):
    description: str
    location: Optional[str] = None
    image_base64: Optional[str] = None


@router.get("/scenarios")
async def list_demo_scenarios():
    return DEMO_SCENARIOS


@router.post("/run-demo")
async def run_autonomous_demo(
    scenario: str = Query("streetlight", description="Scenario key")
):
    try:
        result = await civicfix_agent.run_scenario_demo(scenario_key=scenario, delay_seconds=0.05)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


@router.post("/process-report")
async def process_report(req: ProcessReportRequest):
    try:
        case = await civicfix_agent.ingest_and_process(
            report_text=req.description,
            location_hint=req.location,
            image_base64=req.image_base64
        )
        return {"status": "dispatched", "case": case}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process report: {str(e)}")
