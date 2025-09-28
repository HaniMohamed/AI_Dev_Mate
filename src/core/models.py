# src/core/models.py
from abc import ABC, abstractmethod
from datetime import datetime

class BaseTask(ABC):
    """
    Base class for all tasks in PR assistant.
    """
    def __init__(self, name: str):
        self.name = name
        self.created_at = datetime.now()
        self.completed = False

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def summarize(self) -> str:
        pass
