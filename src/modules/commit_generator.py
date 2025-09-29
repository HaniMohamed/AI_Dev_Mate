# src/modules/commit_generator.py
from src.core.models import BaseTask
from src.services.ollama_service import OllamaService
from src.services.git_service import GitService

class CommitGeneratorTask(BaseTask):
    def __init__(self, ollama: OllamaService):
        super().__init__("Commit Message Generator")
        self.ollama = ollama
        self.commit_message = ""

    def run(self):
        diff = GitService.get_staged_diff()
        if not diff:
            self.commit_message = "No changes to commit."
        else:
            self.commit_message = self.ollama.run_prompt(
                f"Generate a concise commit message for the following diff:\n{diff}"
            )
        self.completed = True

    def summarize(self) -> str:
        return self.commit_message
