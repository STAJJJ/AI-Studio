from functools import lru_cache

from app.core.config import get_settings
from app.core.database import get_session_factory, init_database
from app.services.history.memory_repository import InMemoryWorkflowHistoryRepository
from app.services.history.repository import WorkflowHistoryRepository
from app.services.history.sqlite_repository import SQLiteWorkflowHistoryRepository


@lru_cache
def get_workflow_history_repository() -> WorkflowHistoryRepository:
    settings = get_settings()
    if settings.history_backend == "memory":
        return InMemoryWorkflowHistoryRepository()
    if settings.history_backend == "sqlite":
        init_database(settings)
        return SQLiteWorkflowHistoryRepository(get_session_factory())
    raise ValueError(f"Unsupported history backend: {settings.history_backend}")
