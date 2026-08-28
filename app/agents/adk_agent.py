import logging
from typing import Dict, Any, Optional
import uuid

from app.config import get_settings
from app.models.case import Case, GeminiAnalysis, VerificationResult
from app.services.gemini import gemini_service
from app.agents import tools

logger = logging.getLogger("civicfix.adk")
settings = get_settings()

try:
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False

root_agent = None
adk_runner = None
adk_session_service = None

if ADK_AVAILABLE:
    try:
        root_agent = Agent(
            model=settings.GEMINI_MODEL.replace("models/", ""),
            name="civicfix_root_agent",
            description="Autonomous municipal incident resolution orchestrator",
            instruction=(
                "You are the CivicFix autonomous reasoning agent. Analyze the supplied municipal incident "
                "and produce a concise execution plan. Use Gemini reasoning to identify the issue, priority, "
                "department, evidence requirements, and safe next action. Do not claim a case is resolved "
                "without successful evidence verification. Deterministic CivicFix tools enforce all state-changing "
                "actions and the final closure gate. For an intake reasoning request, do not call state-changing "
                "tools; return a concise plan for the application orchestrator."
            ),
            tools=[
                tools.create_case_tool,
                tools.assign_department_tool,
                tools.create_work_order_tool,
                tools.request_evidence_tool,
                tools.record_verification_tool,
                tools.escalate_case_tool,
                tools.close_case_tool,
            ],
        )
        adk_session_service = InMemorySessionService()
        adk_runner = Runner(
            agent=root_agent,
            app_name="civicfix",
            session_service=adk_session_service,
        )
        logger.info("Google ADK root agent and Runner initialized.")
    except Exception as e:
        logger.warning(f"ADK initialization notice: {e}")
        root_agent = None
        adk_runner = None
        adk_session_service = None


class GoogleADKCivicAgent:
    """CivicFix interface backed by the real Google ADK Agent + Runner."""

    def __init__(self):
        self.model_name = settings.GEMINI_MODEL.replace("models/", "")
        self.agent_name = "civicfix_root_agent"
        self.root_agent = root_agent
        self.runner = adk_runner
        self.session_service = adk_session_service

    def get_adk_definition(self) -> Dict[str, Any]:
        return {
            "name": self.agent_name,
            "model": self.model_name,
            "framework": "Google ADK",
            "adk_native_active": self.root_agent is not None and self.runner is not None,
            "capabilities": ["multimodal_perception", "agent_reasoning", "deterministic_tool_use", "evidence_verification"],
        }

    async def run_reasoning(self, report_text: str, location_hint: Optional[str] = None) -> Optional[str]:
        """Execute the actual ADK agent on the intake path.

        The ADK agent supplies an autonomous reasoning/planning pass. State-changing
        operations remain behind CivicFix's deterministic tools and safety gates.
        """
        if not self.runner or not self.session_service or not settings.GOOGLE_API_KEY:
            return None

        session_id = f"civicfix-{uuid.uuid4().hex[:12]}"
        user_id = "civicfix-system"
        await self.session_service.create_session(
            app_name="civicfix",
            user_id=user_id,
            session_id=session_id,
        )
        prompt = (
            "INTAKE REASONING REQUEST\n"
            f"Citizen report: {report_text}\n"
            f"Location hint: {location_hint or 'Not provided'}\n\n"
            "Return a concise plan covering: issue interpretation, likely priority, responsible department, "
            "recommended action, and evidence required before resolution. Do not call state-changing tools "
            "for this reasoning-only request."
        )
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        final_text = None
        try:
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message,
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = "".join(
                        part.text for part in event.content.parts if getattr(part, "text", None)
                    ).strip()
            return final_text
        except Exception as e:
            logger.warning(f"ADK reasoning execution failed; deterministic path retained: {e}")
            return None

    async def execute_intake(
        self,
        report_text: str,
        location_hint: Optional[str] = None,
        image_base64: Optional[str] = None,
    ) -> tuple[Case, GeminiAnalysis]:
        # Real ADK execution provides the autonomous reasoning pass. The existing
        # Gemini multimodal analysis remains the source of structured case fields.
        adk_reasoning = await self.run_reasoning(report_text, location_hint)
        if adk_reasoning:
            logger.info("ADK reasoning completed for intake: %s", adk_reasoning[:300])

        analysis = await gemini_service.analyze_report(
            text_report=report_text,
            location_hint=location_hint,
            image_base64=image_base64,
        )
        case = await tools.create_case_tool(
            raw_description=report_text,
            location=analysis.location,
            category=analysis.category,
            priority=analysis.priority,
            responsible_department=analysis.responsible_department,
        )
        case.analysis = analysis
        await tools.assign_department_tool(case.id, analysis.responsible_department)

        wo_instructions = (
            f"Remediate {analysis.category.value} at {analysis.location}. "
            f"Recommended actions: {', '.join(analysis.recommended_actions)}"
        )
        await tools.create_work_order_tool(
            case.id,
            analysis.responsible_department,
            wo_instructions,
        )
        return case, analysis

    async def execute_verification(
        self,
        original_problem: str,
        claim_description: str,
        evidence_description: str,
        evidence_image_base64: Optional[str] = None,
    ) -> VerificationResult:
        return await gemini_service.verify_resolution_evidence(
            original_problem=original_problem,
            claim_description=claim_description,
            evidence_description=evidence_description,
            evidence_image_base64=evidence_image_base64,
        )


adk_civic_agent = GoogleADKCivicAgent()
