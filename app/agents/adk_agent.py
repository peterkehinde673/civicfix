import logging
from app.config import get_settings
logger = logging.getLogger("civicfix.adk")
settings = get_settings()

class GoogleADKCivicAgent:
    def __init__(self):
        self.model_name = settings.GEMINI_MODEL.replace("models/", "")
        self.agent_name = "civicfix_root_agent"
    def get_adk_definition(self):
        return {"name": self.agent_name, "model": self.model_name, "framework": "Google ADK 2.0"}

adk_civic_agent = GoogleADKCivicAgent()
