import logging
from typing import Dict, Any
from app.config import get_settings

logger = logging.getLogger("civicfix.adk")
settings = get_settings()


class GoogleADKCivicAgent:
    """Official Google Agent Development Kit (ADK) Agent Interface."""

    def __init__(self):
        self.model_name = settings.GEMINI_MODEL.replace("models/", "")
        self.agent_name = "civicfix_root_agent"
        self.instruction = (
            "You are CivicFix, an Autonomous Community Resolution Engine built on Google ADK.\n"
            "You perceive citizen reports, evaluate visual evidence, dispatch municipal work orders, "
            "reject premature completion claims lacking evidence, and verify resolutions before closure."
        )

    def get_adk_definition(self) -> Dict[str, Any]:
        return {
            "name": self.agent_name,
            "model": self.model_name,
            "instruction": self.instruction,
            "framework": "Google ADK 2.0",
            "capabilities": ["multimodal_perception", "deterministic_tool_use", "evidence_verification"]
        }


adk_civic_agent = GoogleADKCivicAgent()
