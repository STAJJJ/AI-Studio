from abc import ABC, abstractmethod

from app.schemas.task import TaskRecord


class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, task: TaskRecord) -> str:
        """Run task execution and return output file id."""
