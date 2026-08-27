import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.config import get_settings
from app.models.case import Case, AuditEntry, CaseStatus, EvidenceItem, WorkOrder

logger = logging.getLogger("civicfix.firestore")
settings = get_settings()


class FirestoreService:
    """Unified storage interface supporting Firestore and local in-memory storage."""

    def __init__(self):
        self._memory_cases: Dict[str, Case] = {}
        self._case_counter = 0
        self.use_live_firestore = False
        self.db = None

        if not settings.MOCK_FIRESTORE:
            try:
                from google.cloud import firestore
                self.db = firestore.Client(project=settings.GOOGLE_CLOUD_PROJECT)
                self.use_live_firestore = True
                logger.info("Connected to Google Cloud Firestore.")
            except Exception as e:
                logger.warning(f"Failed to connect to live Firestore: {e}. Falling back to in-memory store.")
                self.use_live_firestore = False
        else:
            logger.info("Running with internal persistent in-memory storage (MOCK_FIRESTORE=True).")

    def generate_case_id(self) -> str:
        self._case_counter += 1
        year = datetime.now(timezone.utc).year
        return f"CF-{year}-{self._case_counter:04d}"

    async def create_case(self, case: Case) -> Case:
        now = datetime.now(timezone.utc).isoformat()
        case.updated_at = now
        
        # Add initial audit log
        init_audit = AuditEntry(
            id=str(uuid.uuid4())[:8],
            action="CREATE_CASE",
            details=f"Case {case.id} created: {case.title}",
            metadata={"status": case.status.value, "category": case.category.value}
        )
        case.audit_trail.append(init_audit)

        if self.use_live_firestore and self.db:
            doc_ref = self.db.collection("cases").document(case.id)
            doc_ref.set(case.model_dump())
        
        # Keep in local storage cache
        self._memory_cases[case.id] = case
        logger.info(f"Created case {case.id}")
        return case

    async def get_case(self, case_id: str) -> Optional[Case]:
        if self.use_live_firestore and self.db:
            doc_ref = self.db.collection("cases").document(case_id)
            doc = doc_ref.get()
            if doc.exists:
                return Case.model_validate(doc.to_dict())
            return None
        return self._memory_cases.get(case_id)

    async def list_cases(
        self,
        status: Optional[CaseStatus] = None,
        limit: int = 50
    ) -> List[Case]:
        if self.use_live_firestore and self.db:
            query = self.db.collection("cases").order_by("created_at", direction="DESCENDING")
            if status:
                query = query.where("status", "==", status.value)
            docs = query.limit(limit).stream()
            return [Case.model_validate(doc.to_dict()) for doc in docs]
        
        cases = list(self._memory_cases.values())
        if status:
            cases = [c for c in cases if c.status == status]
        cases.sort(key=lambda x: x.created_at, reverse=True)
        return cases[:limit]

    async def update_case(self, case: Case) -> Case:
        case.updated_at = datetime.now(timezone.utc).isoformat()
        if self.use_live_firestore and self.db:
            doc_ref = self.db.collection("cases").document(case.id)
            doc_ref.set(case.model_dump())
        self._memory_cases[case.id] = case
        return case

    async def add_audit_entry(
        self,
        case_id: str,
        action: str,
        details: str,
        actor: str = "CivicFix Agent",
        metadata: Optional[Dict] = None
    ) -> Optional[AuditEntry]:
        case = await self.get_case(case_id)
        if not case:
            return None
        
        entry = AuditEntry(
            id=str(uuid.uuid4())[:8],
            actor=actor,
            action=action,
            details=details,
            metadata=metadata or {}
        )
        case.audit_trail.append(entry)
        case.last_agent_action = details
        await self.update_case(case)
        return entry

    async def add_evidence(self, case_id: str, evidence: EvidenceItem) -> Optional[Case]:
        case = await self.get_case(case_id)
        if not case:
            return None
        case.evidence.append(evidence)
        await self.add_audit_entry(
            case_id=case_id,
            action="ADD_EVIDENCE",
            details=f"Evidence added: {evidence.description} ({evidence.evidence_type.value})",
            metadata={"evidence_id": evidence.id}
        )
        return await self.update_case(case)

    async def add_work_order(self, case_id: str, work_order: WorkOrder) -> Optional[Case]:
        case = await self.get_case(case_id)
        if not case:
            return None
        case.work_orders.append(work_order)
        await self.add_audit_entry(
            case_id=case_id,
            action="CREATE_WORK_ORDER",
            details=f"Work order {work_order.id} dispatched to {work_order.department}",
            metadata={"work_order_id": work_order.id, "department": work_order.department}
        )
        return await self.update_case(case)

    async def get_metrics(self) -> Dict[str, int]:
        cases = await self.list_cases(limit=500)
        return {
            "total": len(cases),
            "open": sum(1 for c in cases if c.status == CaseStatus.OPEN),
            "investigating": sum(1 for c in cases if c.status == CaseStatus.INVESTIGATING),
            "awaiting_evidence": sum(1 for c in cases if c.status == CaseStatus.AWAITING_EVIDENCE),
            "escalated": sum(1 for c in cases if c.status == CaseStatus.ESCALATED),
            "resolved": sum(1 for c in cases if c.status in [CaseStatus.RESOLVED, CaseStatus.CLOSED]),
        }


# Global Singleton Instance
firestore_service = FirestoreService()
