import logging
import uuid
from typing import Dict, Any, Optional
from app.models.case import (
    Case,
    CaseStatus,
    EvidenceItem,
    EvidenceType,
    WorkOrder,
    IssueCategory,
    PriorityLevel
)
from app.services.firestore import firestore_service
from app.services.departments import department_simulator

logger = logging.getLogger("civicfix.tools")


async def create_case_tool(
    raw_description: str,
    location: str,
    category: IssueCategory,
    priority: PriorityLevel,
    responsible_department: str
) -> Case:
    """Tool: Create an initialized case in Firestore."""
    case_id = firestore_service.generate_case_id()
    new_case = Case(
        id=case_id,
        title=raw_description.strip().split("\n")[0][:70],
        raw_description=raw_description,
        location=location,
        category=category,
        priority=priority,
        status=CaseStatus.OPEN,
        responsible_department=responsible_department,
        workflow_step="CASE_CREATED",
        last_agent_action=f"Case initialized and classified as {category.value} ({priority.value} Priority)"
    )
    return await firestore_service.create_case(new_case)


async def assign_department_tool(case_id: str, department_name: str) -> Optional[Case]:
    """Tool: Route and assign case to municipal department."""
    case = await firestore_service.get_case(case_id)
    if not case:
        return None
    
    case.responsible_department = department_name
    case.status = CaseStatus.INVESTIGATING
    case.workflow_step = "DEPARTMENT_ASSIGNED"
    
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action="ASSIGN_DEPARTMENT",
        details=f"Assigned to {department_name} based on reasoning analysis",
        metadata={"department": department_name}
    )
    return await firestore_service.update_case(case)


async def create_work_order_tool(case_id: str, department_name: str, instructions: str) -> WorkOrder:
    """Tool: Generate and dispatch an official municipal work order."""
    wo = WorkOrder(
        id=f"WO-{uuid.uuid4().hex[:6].upper()}",
        case_id=case_id,
        department=department_name,
        title=f"Dispatch for Case {case_id}",
        instructions=instructions,
        status="DISPATCHED"
    )
    await firestore_service.add_work_order(case_id, wo)
    return wo


async def request_evidence_tool(case_id: str, missing_reason: str) -> Optional[Case]:
    """Tool: Put case in AWAITING_EVIDENCE when resolution claim lacks proof."""
    case = await firestore_service.get_case(case_id)
    if not case:
        return None
    
    case.status = CaseStatus.AWAITING_EVIDENCE
    case.workflow_step = "EVIDENCE_REQUESTED"
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action="REQUEST_EVIDENCE",
        details=f"Resolution claim rejected: {missing_reason}. Formal proof required.",
        metadata={"reason": missing_reason}
    )
    return await firestore_service.update_case(case)


async def escalate_case_tool(case_id: str, escalation_reason: str) -> Optional[Case]:
    """Tool: Escalate unresolved or unresponsive case to Municipal Oversight Board."""
    case = await firestore_service.get_case(case_id)
    if not case:
        return None
    
    case.status = CaseStatus.ESCALATED
    case.escalation_count += 1
    case.workflow_step = "CASE_ESCALATED"
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action="ESCALATE_CASE",
        details=f"Case escalated to Municipal Oversight Board. Reason: {escalation_reason}",
        metadata={"escalation_count": case.escalation_count, "reason": escalation_reason}
    )
    return await firestore_service.update_case(case)


async def verify_resolution_tool(
    case_id: str,
    verification_passed: bool,
    notes: str
) -> Optional[Case]:
    """Tool: Record verification evaluation result on resolution claim."""
    case = await firestore_service.get_case(case_id)
    if not case:
        return None
    
    case.workflow_step = "VERIFICATION_EVALUATED"
    action_type = "VERIFY_RESOLUTION_SUCCESS" if verification_passed else "VERIFY_RESOLUTION_FAILED"
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action=action_type,
        details=notes,
        metadata={"verified": verification_passed}
    )
    return await firestore_service.update_case(case)


async def close_case_tool(case_id: str, closure_notes: str) -> Optional[Case]:
    """Tool: Close case permanently after successful independent verification."""
    case = await firestore_service.get_case(case_id)
    if not case:
        return None
    
    case.status = CaseStatus.RESOLVED
    case.workflow_step = "CASE_RESOLVED"
    case.last_agent_action = "Case verified and resolved successfully."
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action="CLOSE_CASE",
        details=f"Case closed after verified resolution: {closure_notes}",
        metadata={"status": "RESOLVED"}
    )
    return await firestore_service.update_case(case)
