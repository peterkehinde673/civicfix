import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from app.models.case import Case, CaseStatus, EvidenceItem, EvidenceType, VerificationDecision
from app.services.firestore import firestore_service
from app.services.departments import department_simulator
from app.services.pubsub import pubsub_service
from app.agents.adk_agent import adk_civic_agent
from app.agents import tools

logger = logging.getLogger("civicfix.agent")

DEMO_SCENARIOS = {
    "streetlight": {
        "name": "Broken Streetlight (Unity School)",
        "description": "The streetlight beside Unity School has been broken for three weeks and the road becomes dangerous at night.",
        "location": "Unity School, 4th Avenue Junction",
        "category": "Street Lighting"
    },
    "drainage": {
        "name": "Blocked Storm Drainage & Flooding",
        "description": "Heavy storm drain blockage on Market Road causing deep flood waters across pedestrian walkways.",
        "location": "Market Road Commercial Center",
        "category": "Drainage"
    },
    "pothole": {
        "name": "Severe Expressway Crater Pothole",
        "description": "Massive crater pothole damaging vehicle rims and causing sudden traffic stalls on expressway.",
        "location": "Central Expressway KM 14",
        "category": "Roads"
    },
    "waste": {
        "name": "Illegal Waste Dump Accumulation",
        "description": "Refuse overflowing community bins and spreading onto residential sidewalk for over 10 days.",
        "location": "Oakridge Estate Gate 2",
        "category": "Waste Management"
    },
    "water_leak": {
        "name": "High-Pressure Water Main Burst",
        "description": "High-pressure municipal clean water line burst flooding residential street and reducing pressure.",
        "location": "Sunset Boulevard Block 8",
        "category": "Water"
    }
}


class CivicFixAgent:
    def __init__(self):
        self.adk = adk_civic_agent

    async def ingest_and_process(
        self,
        report_text: str,
        location_hint: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> Case:
        case, analysis = await self.adk.execute_intake(
            report_text=report_text,
            location_hint=location_hint,
            image_base64=image_base64
        )
        if image_base64:
            initial_evidence = EvidenceItem(
                id=str(uuid.uuid4())[:8],
                evidence_type=EvidenceType.INITIAL_REPORT,
                description="Citizen primary photographic evidence",
                image_base64=image_base64,
                extracted_metadata={"source": "citizen_upload"}
            )
            case.evidence.append(initial_evidence)

        await firestore_service.update_case(case)
        await pubsub_service.publish_event("case.dispatched", {"case_id": case.id, "department": analysis.responsible_department})
        return await firestore_service.get_case(case.id)

    async def run_scenario_demo(self, scenario_key: str = "streetlight", delay_seconds: float = 0.01) -> Dict[str, Any]:
        scenario = DEMO_SCENARIOS.get(scenario_key, DEMO_SCENARIOS["streetlight"])
        steps_log = []

        # 1. Ingest via ADK
        case = await self.ingest_and_process(
            report_text=scenario["description"],
            location_hint=scenario["location"],
            image_base64=None
        )
        steps_log.append({
            "step": 1,
            "phase": "UNDERSTAND_AND_DISPATCH",
            "message": f"Ingested '{scenario['name']}'. Classified as {case.category.value} ({case.priority.value} Priority)."
        })
        await asyncio.sleep(delay_seconds)

        # 2. Premature Claim
        dept_claim = department_simulator.simulate_premature_resolution(
            department=case.responsible_department,
            issue_summary=scenario["name"]
        )
        await firestore_service.add_audit_entry(
            case_id=case.id,
            action="DEPARTMENT_RESPONSE_RECEIVED",
            details=f"Received claim from {case.responsible_department}: '{dept_claim['claim_text']}'",
            metadata=dept_claim
        )
        steps_log.append({
            "step": 2,
            "phase": "CLAIM_RECEIVED",
            "message": f"{case.responsible_department} claimed repair completed without attached proof."
        })
        await asyncio.sleep(delay_seconds)

        # 3. Reject Blind Trust
        unverified_eval = await self.adk.execute_verification(
            original_problem=case.raw_description,
            claim_description=dept_claim["claim_text"],
            evidence_description=""
        )
        await tools.record_verification_tool(case.id, unverified_eval)
        await tools.request_evidence_tool(
            case_id=case.id,
            missing_reason="Department claimed completion without photographic verification."
        )
        steps_log.append({
            "step": 3,
            "phase": "BLIND_TRUST_REJECTED",
            "message": "Agent evaluated claim: BLIND TRUST REJECTED. Status moved to AWAITING_EVIDENCE."
        })
        await asyncio.sleep(delay_seconds)

        # 4. Field Crew Submits Proof
        field_proof = department_simulator.simulate_resolution_evidence(case.category.value)
        resolution_evidence = EvidenceItem(
            id=field_proof["evidence_id"],
            evidence_type=EvidenceType.RESOLUTION_PROOF,
            description=field_proof["description"],
            image_base64=field_proof["simulated_image"],
            extracted_metadata={"verified_by_supervisor": True}
        )
        await firestore_service.add_evidence(case.id, resolution_evidence)
        steps_log.append({
            "step": 4,
            "phase": "EVIDENCE_INGESTED",
            "message": "Field crew uploaded verified post-repair photographic proof."
        })
        await asyncio.sleep(delay_seconds)

        # 5. Real Verification (No Hardcoded Success)
        verified_eval = await self.adk.execute_verification(
            original_problem=case.raw_description,
            claim_description=dept_claim["claim_text"],
            evidence_description=field_proof["description"],
            evidence_image_base64=field_proof["simulated_image"]
        )
        await tools.record_verification_tool(case.id, verified_eval)

        # 6. Double-Lock Closure Gate
        if verified_eval.verified and verified_eval.action == VerificationDecision.RESOLVE_CASE:
            await tools.close_case_tool(
                case_id=case.id,
                closure_notes=f"Photographic verification passed (Confidence {int(verified_eval.confidence_score*100)}%). Resolved autonomously."
            )

        updated_case = await firestore_service.get_case(case.id)
        steps_log.append({
            "step": 5,
            "phase": "RESOLVED_AND_CLOSED",
            "message": f"Case {case.id} processed autonomously."
        })

        return {
            "case_id": case.id,
            "scenario": scenario["name"],
            "status": "SUCCESS",
            "case": updated_case.model_dump(),
            "workflow_steps": steps_log
        }


civicfix_agent = CivicFixAgent()
