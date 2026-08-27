from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CivicFix"
    APP_SUBTITLE: str = "Autonomous Community Resolution Engine"
    ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Google Cloud & Gemini Settings
    GOOGLE_API_KEY: str = "AIzaSyA5_OMhm2Lc87qEAWzzpHSKu3ixIr_z9z8"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GOOGLE_CLOUD_PROJECT: str = "civicfix-demo"
    FIRESTORE_DATABASE: str = "(default)"
    
    # Operation Flags
    DEMO_MODE: bool = True
    MOCK_FIRESTORE: bool = True
    MOCK_PUBSUB: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
