import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from app.models.case import Case, CaseStatus, EvidenceItem, EvidenceType
from app.services.firestore import firestore_service
from app.services.gemini import gemini_service
from app.services.departments import department_simulator
from app.services.pubsub import pubsub_service
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
    async def ingest_and_process(
        self,
        report_text: str,
        location_hint: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> Case:
        analysis = await gemini_service.analyze_report(
            text_report=report_text,
            location_hint=location_hint,
            image_base64=image_base64
        )
        case = await tools.create_case_tool(
            raw_description=report_text,
            location=analysis.location,
            category=analysis.category,
            priority=analysis.priority,
            responsible_department=analysis.responsible_department
        )
        case.analysis = analysis

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
        await tools.assign_department_tool(case.id, analysis.responsible_department)

        wo_instructions = (
            f"Remediate {analysis.category.value} at {analysis.location}. "
            f"Recommended actions: {', '.join(analysis.recommended_actions)}"
        )
        await tools.create_work_order_tool(case.id, analysis.responsible_department, wo_instructions)
        await pubsub_service.publish_event("case.dispatched", {"case_id": case.id, "department": analysis.responsible_department})
        return await firestore_service.get_case(case.id)

    async def run_scenario_demo(self, scenario_key: str = "streetlight", delay_seconds: float = 0.05) -> Dict[str, Any]:
        scenario = DEMO_SCENARIOS.get(scenario_key, DEMO_SCENARIOS["streetlight"])
        steps_log = []

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
            "message": f"{case.responsible_department} claimed repair completed without evidence."
        })
        await asyncio.sleep(delay_seconds)

        unverified_eval = await gemini_service.verify_resolution_evidence(
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

        verified_eval = await gemini_service.verify_resolution_evidence(
            original_problem=case.raw_description,
            claim_description=dept_claim["claim_text"],
            evidence_description=field_proof["description"],
            evidence_image_base64=field_proof["simulated_image"]
        )
        await tools.record_verification_tool(case.id, verified_eval)

        await tools.close_case_tool(
            case_id=case.id,
            closure_notes=f"Photographic verification passed (Confidence {int(verified_eval.confidence_score*100)}%). Resolved autonomously."
        )

        updated_case = await firestore_service.get_case(case.id)
        steps_log.append({
            "step": 5,
            "phase": "RESOLVED_AND_CLOSED",
            "message": f"Case {case.id} verified and resolved autonomously."
        })

        return {
            "case_id": case.id,
            "scenario": scenario["name"],
            "status": "SUCCESS",
            "case": updated_case.model_dump(),
            "workflow_steps": steps_log
        }


civicfix_agent = CivicFixAgent()
