from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DEFAULT_DB_URL = f"sqlite:///{DATA_DIR / 'fcfea.db'}"
DEFAULT_LOG_FILE = str(LOG_DIR / "app.log")


class Settings(BaseSettings):
    app_name: str = "FCFEA"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:8501"]
    database_url: str = DEFAULT_DB_URL
    log_level: str = "INFO"
    log_file: str = DEFAULT_LOG_FILE
    openai_api_key: str | None = None
    openai_model_name: str = "gpt-4o-mini"
    openai_timeout_seconds: int = 20
    openai_max_retries: int = 1
    # Backward compatibility for existing .env files; no longer used by provider logic.
    gemini_api_key: str | None = None
    gemini_model_name: str | None = None
    gemini_timeout_seconds: int | None = None
    gemini_max_retries: int | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
