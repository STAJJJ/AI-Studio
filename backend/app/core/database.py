from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings, get_settings


class Base(DeclarativeBase):
    pass


def create_sqlite_engine(database_url: str) -> Engine:
    _ensure_sqlite_parent_dir(database_url)
    return create_engine(database_url, connect_args={"check_same_thread": False})


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    if settings.history_backend != "sqlite":
        raise ValueError(f"Database engine is only available for sqlite history backend: {settings.history_backend}")
    return create_sqlite_engine(settings.database_url)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return create_session_factory(get_engine())


def init_database(settings: Settings | None = None) -> None:
    resolved = settings or get_settings()
    if resolved.history_backend != "sqlite":
        return

    from app.models import workflow_run  # noqa: F401 - import registers ORM mappings.

    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix) or database_url == "sqlite:///:memory:":
        return
    database_path = Path(database_url.removeprefix(prefix))
    database_path.parent.mkdir(parents=True, exist_ok=True)
