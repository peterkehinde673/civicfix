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
    PriorityLevel,
    VerificationResult
)
from app.services.firestore import firestore_service

logger = logging.getLogger("civicfix.tools")


async def create_case_tool(
    raw_description: str,
    location: str,
    category: IssueCategory,
    priority: PriorityLevel,
    responsible_department: str
) -> Case:
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
        last_agent_action=f"Classified as {category.value} ({priority.value} Priority)"
    )
    return await firestore_service.create_case(new_case)


async def assign_department_tool(case_id: str, department_name: str) -> Optional[Case]:
    case = await firestore_service.get_case(case_id)
    if not case:
        return None
    case.responsible_department = department_name
    case.status = CaseStatus.INVESTIGATING
    case.workflow_step = "DEPARTMENT_ASSIGNED"
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action="ASSIGN_DEPARTMENT",
        details=f"Assigned to {department_name}",
        metadata={"department": department_name}
    )
    return await firestore_service.update_case(case)


async def create_work_order_tool(case_id: str, department_name: str, instructions: str) -> WorkOrder:
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
    case = await firestore_service.get_case(case_id)
    if not case:
        return None
    case.status = CaseStatus.AWAITING_EVIDENCE
    case.workflow_step = "EVIDENCE_REQUESTED"
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action="REQUEST_EVIDENCE",
        details=f"Resolution claim rejected: {missing_reason}",
        metadata={"reason": missing_reason}
    )
    return await firestore_service.update_case(case)


async def record_verification_tool(case_id: str, verification: VerificationResult) -> Optional[Case]:
    case = await firestore_service.get_case(case_id)
    if not case:
        return None
    case.verification_history.append(verification)
    action_name = "VERIFY_RESOLUTION_SUCCESS" if verification.verified else "VERIFY_RESOLUTION_FAILED"
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action=action_name,
        details=f"Verification score {int(verification.confidence_score*100)}%: {verification.reason}",
        metadata={"confidence": verification.confidence_score, "action": verification.action.value}
    )
    return await firestore_service.update_case(case)


async def escalate_case_tool(case_id: str, escalation_reason: str) -> Optional[Case]:
    case = await firestore_service.get_case(case_id)
    if not case:
        return None
    case.status = CaseStatus.ESCALATED
    case.escalation_count += 1
    case.workflow_step = "CASE_ESCALATED"
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action="ESCALATE_CASE",
        details=f"Escalated to Municipal Oversight Board: {escalation_reason}",
        metadata={"count": case.escalation_count}
    )
    return await firestore_service.update_case(case)


async def close_case_tool(case_id: str, closure_notes: str) -> Optional[Case]:
    case = await firestore_service.get_case(case_id)
    if not case:
        return None
    case.status = CaseStatus.RESOLVED
    case.workflow_step = "CASE_RESOLVED"
    case.last_agent_action = "Case verified & resolved autonomously."
    await firestore_service.add_audit_entry(
        case_id=case_id,
        action="CLOSE_CASE",
        details=f"Case closed: {closure_notes}",
        metadata={"status": "RESOLVED"}
    )
    return await firestore_service.update_case(case)
