from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.agents.civicfix_agent import civicfix_agent
from app.services.firestore import firestore_service

router = APIRouter(prefix="/api/orchestrator", tags=["Autonomous Orchestrator"])


class ProcessReportRequest(BaseModel):
    description: str
    location: Optional[str] = None
    image_base64: Optional[str] = None


@router.post("/run-demo")
async def run_autonomous_demo():
    """
    Executes the full end-to-end autonomous resolution demo cycle:
    Perception -> Reasoning -> Routing -> Premature Claim -> Proof Rejection -> Evidence Ingestion -> Verification -> Case Closure.
    """
    try:
        result = await civicfix_agent.run_killer_demo_sequence(delay_seconds=0.2)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autonomous demo workflow failed: {str(e)}")


@router.post("/process-report")
async def process_report(req: ProcessReportRequest):
    """
    Ingests any live user community report and triggers the initial autonomous routing loop.
    """
    try:
        case = await civicfix_agent.ingest_and_process(
            report_text=req.description,
            location_hint=req.location,
            image_base64=req.image_base64
        )
        return {"status": "dispatched", "case": case}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process citizen report: {str(e)}")
