# src/modules/code_review.py
from core.models import BaseTask
from services.ollama_service import OllamaService
from services.git_service import GitService

class CodeReviewTask(BaseTask):
    def __init__(self, ollama: OllamaService):
        super().__init__("Code Review")
        self.ollama = ollama
        self.review = ""

    def run(self):
        diff = GitService.get_staged_diff()
        if not diff:
            self.review = "No staged changes to review."
        else:
            self.review = self.ollama.run_prompt(f"Review this diff:\n{diff}")
        self.completed = True

    def summarize(self) -> str:
        return self.review
