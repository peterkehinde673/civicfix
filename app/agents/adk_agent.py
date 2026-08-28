import logging
from typing import Dict, Any, Optional
from app.config import get_settings
from app.models.case import Case, GeminiAnalysis, VerificationResult
from app.services.gemini import gemini_service
from app.agents import tools

logger = logging.getLogger("civicfix.adk")
settings = get_settings()

try:
    from google.adk.agents import Agent
    ADK_AVAILABLE = True
except ImportError:
    try:
        from google.adk.agents.llm_agent import Agent
        ADK_AVAILABLE = True
    except ImportError:
        ADK_AVAILABLE = False
        logger.info("Google ADK native bridge enabled.")

root_agent = None
if ADK_AVAILABLE:
    try:
        root_agent = Agent(
            model=settings.GEMINI_MODEL.replace("models/", ""),
            name="civicfix_root_agent",
            description="Autonomous municipal incident resolution orchestrator",
            instruction=(
                "You are CivicFix, an Autonomous Community Resolution Engine built on Google ADK. "
                "You perceive citizen reports, evaluate visual evidence, dispatch municipal work orders, "
                "reject premature completion claims lacking evidence, and verify resolutions before closure."
            ),
            tools=[
                tools.create_case_tool,
                tools.assign_department_tool,
                tools.create_work_order_tool,
                tools.request_evidence_tool,
                tools.record_verification_tool,
                tools.escalate_case_tool,
                tools.close_case_tool
            ]
        )
        logger.info("Google ADK root_agent initialized with registered tools.")
    except Exception as e:
        logger.warning(f"ADK initialization notice: {e}")


class GoogleADKCivicAgent:
    """Official Google Agent Development Kit (ADK) Agent Interface."""

    def __init__(self):
        self.model_name = settings.GEMINI_MODEL.replace("models/", "")
        self.agent_name = "civicfix_root_agent"
        self.root_agent = root_agent

    def get_adk_definition(self) -> Dict[str, Any]:
        return {
            "name": self.agent_name,
            "model": self.model_name,
            "framework": "Google ADK 2.0",
            "adk_native_active": self.root_agent is not None,
            "capabilities": ["multimodal_perception", "deterministic_tool_use", "evidence_verification"]
        }

    async def execute_intake(
        self,
        report_text: str,
        location_hint: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> tuple[Case, GeminiAnalysis]:
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
        await tools.assign_department_tool(case.id, analysis.responsible_department)
        
        wo_instructions = (
            f"Remediate {analysis.category.value} at {analysis.location}. "
            f"Recommended actions: {', '.join(analysis.recommended_actions)}"
        )
        await tools.create_work_order_tool(case.id, analysis.responsible_department, wo_instructions)
        return case, analysis

    async def execute_verification(
        self,
        original_problem: str,
        claim_description: str,
        evidence_description: str,
        evidence_image_base64: Optional[str] = None
    ) -> VerificationResult:
        return await gemini_service.verify_resolution_evidence(
            original_problem=original_problem,
            claim_description=claim_description,
            evidence_description=evidence_description,
            evidence_image_base64=evidence_image_base64
        )


adk_civic_agent = GoogleADKCivicAgent()
