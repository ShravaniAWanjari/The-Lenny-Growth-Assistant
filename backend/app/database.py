import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Locate root .env file if running from backend or project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql://lenny:lenny_dev_password@localhost:5432/lenny"
    gemini_api_key: str = ""
    llm_provider: str = "gemini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    pi_agent_url: str = "http://localhost:3001"
    pi_agent_port: int = 3001
    artifact_sanitization_mode: str = "sanitize"  # "sanitize" or "reject"
    allowed_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
