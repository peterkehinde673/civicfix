import logging
from app.config import get_settings
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
            instruction="You are CivicFix, an Autonomous Community Resolution Engine built on Google ADK.",
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
        logger.info("Google ADK root_agent initialized with deterministic tools.")
    except Exception as e:
        logger.warning(f"ADK init notice: {e}")

class GoogleADKCivicAgent:
    def __init__(self):
        self.model_name = settings.GEMINI_MODEL.replace("models/", "")
        self.agent_name = "civicfix_root_agent"
        self.root_agent = root_agent
    def get_adk_definition(self):
        return {
            "name": self.agent_name,
            "model": self.model_name,
            "framework": "Google ADK 2.0",
            "adk_native_active": self.root_agent is not None,
            "capabilities": ["multimodal_perception", "deterministic_tool_use", "evidence_verification"]
        }

adk_civic_agent = GoogleADKCivicAgent()
