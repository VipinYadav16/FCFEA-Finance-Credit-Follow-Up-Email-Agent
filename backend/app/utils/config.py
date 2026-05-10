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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
