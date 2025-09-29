# src/modules/repo_indexer_task.py
from typing import Optional
from src.core.models import BaseTask
from src.services.repo_indexer import RepoIndexer
from src.services.ollama_service import OllamaService


class RepoIndexTask(BaseTask):
    def __init__(self, path: Optional[str] = None):
        super().__init__(name="repo_indexer")
        self.path = path
        self._index = None
        self._summ = ""

    def run(self):
        if not self.path:
            self.path = input("Enter path to repository to index: ").strip()
        yn = input("Generate per-file AI context? This can be slow. [y/N]: ").strip().lower()
        with_context = yn in ("y", "yes")
        ollama = OllamaService() if with_context else None
        idx = RepoIndexer(ollama=ollama)
        self._index = idx.index(self.path, generate_context=with_context)
        self._summ = idx.summarize(self._index)
        self.completed = True

    def summarize(self) -> str:
        return self._summ or "No summary available."
