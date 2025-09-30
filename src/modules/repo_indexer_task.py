# src/modules/repo_indexer_task.py
from typing import Optional
from src.core.models import BaseTask
from src.services.repo_indexer import RepoIndexer
from src.services.ollama_service import OllamaService
from src.core.exceptions import IndexError
from src.utils.console import aidm_console


class RepoIndexTask(BaseTask):
    def __init__(self, path: Optional[str] = None, force_refresh: bool = False):
        super().__init__(name="repo_indexer")
        self.path = path
        self.force_refresh = force_refresh
        self._index = None
        self._summ = ""

    def run(self):
        """Run the repository indexing task with beautiful output."""
        if not self.path:
            self.path = aidm_console.prompt("Enter path to repository to index")
        
        aidm_console.print_header("📁 Repository Indexing", f"Target: {self.path}")
        
        ollama = OllamaService()
        idx = RepoIndexer(ollama=ollama)
        
        # Check if index already exists and is valid
        if idx.index_exists(self.path) and idx.is_index_valid(self.path) and not self.force_refresh:
            aidm_console.print_success("Index already exists and is up-to-date.")
            if not aidm_console.confirm("Do you want to regenerate it anyway?", default=False):
                self._index = idx.load_index(self.path)
                self._summ = idx.summarize(self._index)
                self.completed = True
                return
        
        # Ask about context generation
        with_context = aidm_console.confirm("Generate per-file AI context? This can be slow.", default=False)
        
        try:
            aidm_console.print_primary("Starting repository indexing...")
            self._index = idx.index(self.path, generate_context=with_context, show_progress=True)
            self._summ = idx.summarize(self._index)
            self.completed = True
            aidm_console.print_success("Repository indexing completed successfully!")
        except Exception as e:
            aidm_console.print_error(f"Failed to index repository: {e}")
            raise IndexError(f"Failed to index repository: {e}")

    def summarize(self) -> str:
        return self._summ or "No summary available."
