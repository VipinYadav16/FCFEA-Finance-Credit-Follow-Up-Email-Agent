from pathlib import Path

from app.db.session import Base, engine
from app.models import orm  # noqa: F401
from app.utils.config import settings


def init_db() -> None:
    db_path = None
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.replace("sqlite:///", "")
    if db_path:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
