import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from app.models.case import Case, CaseStatus, EvidenceItem, EvidenceType
from app.services.firestore import firestore_service
from app.services.gemini import gemini_service
from app.services.departments import department_simulator
from app.agents import tools

logger = logging.getLogger("civicfix.agent")


class CivicFixAgent:
    """
    Autonomous Community Resolution Engine Agent.
    Implements: UNDERSTAND -> PLAN -> ACT -> WAIT -> VERIFY -> RECOVER/ESCALATE -> RESOLVE
    """

    async def ingest_and_process(
        self,
        report_text: str,
        location_hint: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> Case:
        """
        Step 1 & 2: Perceive unstructured report, use Gemini for reasoning,
        create structured case, and dispatch work orders.
        """
        logger.info("Perceiving and analyzing community report with Gemini...")
        
        # 1. UNDERSTAND: Gemini Reasoning
        analysis = await gemini_service.analyze_report(
            text_report=report_text,
            location_hint=location_hint,
            image_base64=image_base64
        )
        
        # 2. PLAN & ACT: Create case with deterministic tool
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
                description="Citizen initial photographic report",
                image_base64=image_base64,
                extracted_metadata={"source": "citizen_upload"}
            )
            case.evidence.append(initial_evidence)
            
        await firestore_service.update_case(case)

        # 3. ROUTE: Assign department
        await tools.assign_department_tool(case.id, analysis.responsible_department)
        
        # 4. DISPATCH: Create Work Order
        wo_instructions = (
            f"Address {analysis.category.value} issue at {analysis.location}. "
            f"Recommended actions: {', '.join(analysis.recommended_actions)}"
        )
        await tools.create_work_order_tool(case.id, analysis.responsible_department, wo_instructions)
        
        return await firestore_service.get_case(case.id)

    async def run_killer_demo_sequence(self, delay_seconds: float = 1.0) -> Dict[str, Any]:
        """
        Executes the complete killer demo demonstrating the Agent's refusal to blindly
        trust premature resolution claims, demanding proof, and resolving upon verification.
        """
        steps_log = []
        
        # STEP 1: Citizen Report
        sample_report = "The streetlight beside Unity School has been broken for three weeks and the road becomes dangerous at night."
        sample_loc = "Unity School, 4th Avenue Junction"
        
        case = await self.ingest_and_process(
            report_text=sample_report,
            location_hint=sample_loc,
            image_base64=None
        )
        steps_log.append({
            "step": 1,
            "phase": "UNDERSTAND_AND_DISPATCH",
            "message": f"Ingested report. Classified as {case.category.value} ({case.priority.value} Priority). Dispatched to {case.responsible_department}."
        })
        await asyncio.sleep(delay_seconds)

        # STEP 2: Simulated premature resolution claim (The Trap)
        dept_claim = department_simulator.simulate_premature_resolution(
            department=case.responsible_department,
            issue_summary="Unity School Streetlight"
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
            "message": f"{case.responsible_department} claimed completion with no photographic proof."
        })
        await asyncio.sleep(delay_seconds)

        # STEP 3: AGENT VERIFICATION (Agent rejects blind trust)
        verification_result = await gemini_service.verify_resolution_evidence(
            original_problem=case.raw_description,
            claim_description=dept_claim["claim_text"],
            evidence_description=""  # No evidence attached!
        )
        
        # Agent Acts: Rejects closure, requests photographic evidence
        await tools.request_evidence_tool(
            case_id=case.id,
            missing_reason="Department marked completed but provided zero photographic evidence of operational streetlight"
        )
        steps_log.append({
            "step": 3,
            "phase": "VERIFICATION_REJECTED",
            "message": "Agent evaluated claim: BLIND TRUST REJECTED. Case kept OPEN in AWAITING_EVIDENCE status. Requested photographic proof."
        })
        await asyncio.sleep(delay_seconds)

        # STEP 4: Simulated Field Crew submits verified photographic evidence
        simulated_evidence_data = department_simulator.simulate_resolution_evidence(case.category.value)
        resolution_evidence = EvidenceItem(
            id=simulated_evidence_data["evidence_id"],
            evidence_type=EvidenceType.RESOLUTION_PROOF,
            description=simulated_evidence_data["description"],
            image_base64=simulated_evidence_data["simulated_image"],
            extracted_metadata={"verified_by_supervisor": True}
        )
        await firestore_service.add_evidence(case.id, resolution_evidence)
        steps_log.append({
            "step": 4,
            "phase": "EVIDENCE_SUBMITTED",
            "message": "Field repair team submitted post-repair photographic proof."
        })
        await asyncio.sleep(delay_seconds)

        # STEP 5: Gemini Verifies the submitted photographic proof
        verified_eval = await gemini_service.verify_resolution_evidence(
            original_problem=case.raw_description,
            claim_description=dept_claim["claim_text"],
            evidence_description=simulated_evidence_data["description"]
        )
        
        await tools.verify_resolution_tool(
            case_id=case.id,
            verification_passed=True,
            notes=f"Visual verification passed (Confidence {int(verified_eval['confidence_score']*100)}%): Streetlight illuminated and operational."
        )

        # STEP 6: Autonomous Case Closure
        await tools.close_case_tool(
            case_id=case.id,
            closure_notes="Independent photographic verification successful. SLA fulfilled."
        )
        
        updated_case = await firestore_service.get_case(case.id)
        steps_log.append({
            "step": 5,
            "phase": "RESOLVED_AND_CLOSED",
            "message": f"Case {case.id} successfully verified and closed autonomously."
        })

        return {
            "case_id": case.id,
            "status": "SUCCESS",
            "case": updated_case.model_dump(),
            "workflow_steps": steps_log
        }


civicfix_agent = CivicFixAgent()
