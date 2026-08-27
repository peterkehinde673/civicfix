import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.models.case import (
    Case,
    CaseCreateRequest,
    CaseStatus,
    EvidenceItem,
    EvidenceType,
    IssueCategory,
    PriorityLevel,
)
from app.services.firestore import firestore_service

router = APIRouter(prefix="/api", tags=["Cases"])


@router.get("/stats")
async def get_dashboard_stats():
    """Retrieve aggregate status counts for the dashboard metric cards."""
    return await firestore_service.get_metrics()


@router.get("/cases", response_model=List[Case])
async def list_cases(
    status_filter: Optional[CaseStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
):
    """List all community cases with optional status filter."""
    return await firestore_service.list_cases(status=status_filter, limit=limit)


@router.post("/cases", response_model=Case, status_code=status.HTTP_201_CREATED)
async def create_case(req: CaseCreateRequest):
    """Manually or preliminarily create a case record."""
    case_id = firestore_service.generate_case_id()
    
    # Generate human readable title from first 60 chars of report
    summary_title = req.description.strip().split("\n")[0][:60]
    if len(req.description) > 60:
        summary_title += "..."

    evidence_items = []
    if req.image_base64:
        evidence_items.append(
            EvidenceItem(
                id=str(uuid.uuid4())[:8],
                evidence_type=EvidenceType.INITIAL_REPORT,
                description="Initial user photographic evidence",
                image_base64=req.image_base64,
            )
        )

    new_case = Case(
        id=case_id,
        title=summary_title,
        raw_description=req.description,
        location=req.location or "Pending classification",
        status=CaseStatus.OPEN,
        evidence=evidence_items,
        workflow_step="REPORTED",
        last_agent_action="Case submitted by community member",
    )

    return await firestore_service.create_case(new_case)


@router.get("/cases/{case_id}", response_model=Case)
async def get_case(case_id: str):
    """Retrieve full case details, history, evidence, and audit logs."""
    case = await firestore_service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found"
        )
    return case


@router.patch("/cases/{case_id}/status", response_model=Case)
async def update_case_status(
    case_id: str,
    new_status: CaseStatus,
    reason: str = Query("Status updated by orchestrator")
):
    """Update case status and append audit record."""
    case = await firestore_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    old_status = case.status
    case.status = new_status
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action="UPDATE_STATUS",
        details=f"Status changed from {old_status.value} to {new_status.value}. Reason: {reason}",
        metadata={"old_status": old_status.value, "new_status": new_status.value}
    )
    return await firestore_service.update_case(case)
