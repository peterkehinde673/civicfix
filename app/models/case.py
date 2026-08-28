from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IssueCategory(str, Enum):
    ROADS = "Roads"
    DRAINAGE = "Drainage"
    STREET_LIGHTING = "Street Lighting"
    WASTE_MANAGEMENT = "Waste Management"
    PUBLIC_SAFETY = "Public Safety"
    WATER = "Water"
    PUBLIC_FACILITIES = "Public Facilities"
    OTHER = "Other"


class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CaseStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    AWAITING_EVIDENCE = "AWAITING_EVIDENCE"
    ESCALATED = "ESCALATED"
    RESOLUTION_PROPOSED = "RESOLUTION_PROPOSED"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class EvidenceType(str, Enum):
    INITIAL_REPORT = "INITIAL_REPORT"
    ADDITIONAL_USER = "ADDITIONAL_USER"
    DEPARTMENT_CLAIM = "DEPARTMENT_CLAIM"
    RESOLUTION_PROOF = "RESOLUTION_PROOF"


class VerificationDecision(str, Enum):
    RESOLVE_CASE = "RESOLVE_CASE"
    REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
    ESCALATE_CASE = "ESCALATE_CASE"


class EvidenceItem(BaseModel):
    id: str
    evidence_type: EvidenceType = EvidenceType.INITIAL_REPORT
    description: str
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    mime_type: Optional[str] = "image/jpeg"
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict)
    verified: Optional[bool] = None
    verification_notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditEntry(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: str = "CivicFix Agent"
    action: str
    details: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkOrder(BaseModel):
    id: str
    case_id: str
    department: str
    title: str
    instructions: str
    status: str = "DISPATCHED"
    dispatched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    department_notes: Optional[str] = None
    claimed_resolution_at: Optional[str] = None


class GeminiAnalysis(BaseModel):
    problem_summary: str = ""
    category: IssueCategory = IssueCategory.OTHER
    location: str = "Unknown"
    severity: str = "MEDIUM"
    priority: PriorityLevel = PriorityLevel.MEDIUM
    responsible_department: str = "Public Facilities Department"
    evidence_available: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    visual_observations: List[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    verified: bool
    confidence_score: float = Field(default=0.9, ge=0.0, le=1.0)
    reason: str = "Evidence verified against defect."
    evidence_quality: str = "SUFFICIENT"
    action: VerificationDecision = VerificationDecision.RESOLVE_CASE


class CaseCreateRequest(BaseModel):
    description: str
    location: Optional[str] = None
    image_base64: Optional[str] = None
    reporter_contact: Optional[str] = None


class Case(BaseModel):
    id: str
    title: str
    raw_description: str
    location: str
    category: IssueCategory = IssueCategory.OTHER
    priority: PriorityLevel = PriorityLevel.MEDIUM
    status: CaseStatus = CaseStatus.OPEN
    responsible_department: Optional[str] = None
    analysis: Optional[GeminiAnalysis] = None
    evidence: List[EvidenceItem] = Field(default_factory=list)
    work_orders: List[WorkOrder] = Field(default_factory=list)
    audit_trail: List[AuditEntry] = Field(default_factory=list)
    workflow_step: str = "INITIALIZED"
    last_agent_action: str = "Report received"
    escalation_count: int = 0
    verification_history: List[VerificationResult] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None
