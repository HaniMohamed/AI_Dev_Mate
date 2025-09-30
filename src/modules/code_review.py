# src/modules/code_review.py
from src.core.models import BaseTask
from src.core.utils import check_and_load_index
from src.services.ollama_service import OllamaService
from src.services.git_service import GitService
from src.utils.console import aidm_console

class CodeReviewTask(BaseTask):
    def __init__(self, ollama: OllamaService):
        super().__init__("Code Review")
        self.ollama = ollama
        self.review = ""

    def run(self):
        """Run code review with beautiful output."""
        aidm_console.print_header("🔍 Code Review", "Analyzing staged changes")
        
        # Check if indexed data is available
        index_data = check_and_load_index(ollama=self.ollama)
        if index_data is None:
            self.review = "Code review failed: No indexed data available. Please index the project first."
            self.completed = True
            return
        
        try:
            diff = GitService.get_staged_diff()
            if not diff:
                aidm_console.print_warning("No staged changes to review.")
                self.review = "No staged changes to review."
            else:
                aidm_console.print_info("Analyzing staged changes with AI...")
                
                # Show the diff with syntax highlighting
                aidm_console.print_primary("Staged Changes:")
                aidm_console.print_code_syntax(diff, "diff")
                
                # Generate review using indexed context
                with aidm_console.create_progress("Generating review") as progress:
                    task = progress.add_task("Analyzing code...", total=100)
                    # Include project context from index for better review
                    project_context = f"Project context: {index_data.get('summary', {}).get('languages', {})}"
                    self.review = self.ollama.run_prompt(f"{project_context}\n\nReview this diff:\n{diff}")
                    progress.update(task, completed=100)
                
                aidm_console.print_success("Code review completed!")
        except Exception as e:
            aidm_console.print_error(f"Code review failed: {e}")
            self.review = f"Code review failed: {e}"
        
        self.completed = True

    def summarize(self) -> str:
        """Return review summary with beautiful formatting."""
        if self.review:
            aidm_console.print_separator()
            aidm_console.print_header("📋 Review Summary", "AI-generated code analysis")
            aidm_console.print_markdown(self.review)
        return self.review
