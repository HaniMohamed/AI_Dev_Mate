# src/modules/commit_generator.py
from src.core.models import BaseTask
from src.services.ollama_service import OllamaService
from src.services.git_service import GitService
from src.utils.console import aidm_console

class CommitGeneratorTask(BaseTask):
    def __init__(self, ollama: OllamaService):
        super().__init__("Commit Message Generator")
        self.ollama = ollama
        self.commit_message = ""

    def run(self):
        """Run commit message generation with beautiful output."""
        aidm_console.print_header("📝 Commit Generator", "Generating intelligent commit message")
        
        try:
            diff = GitService.get_staged_diff()
            if not diff:
                aidm_console.print_warning("No staged changes to commit.")
                self.commit_message = "No changes to commit."
            else:
                aidm_console.print_info("Analyzing staged changes...")
                
                # Show the diff with syntax highlighting
                aidm_console.print_primary("Staged Changes:")
                aidm_console.print_code_syntax(diff, "diff")
                
                # Generate commit message
                with aidm_console.create_progress("Generating commit message") as progress:
                    task = progress.add_task("Analyzing changes...", total=100)
                    self.commit_message = self.ollama.run_prompt(
                        f"Generate a concise commit message for the following diff:\n{diff}"
                    )
                    progress.update(task, completed=100)
                
                aidm_console.print_success("Commit message generated!")
        except Exception as e:
            aidm_console.print_error(f"Commit generation failed: {e}")
            self.commit_message = f"Commit generation failed: {e}"
        
        self.completed = True

    def summarize(self) -> str:
        """Return commit message with beautiful formatting."""
        if self.commit_message:
            aidm_console.print_separator()
            aidm_console.print_header("📋 Generated Commit Message", "AI-powered commit message")
            aidm_console.print_markdown(f"```\n{self.commit_message}\n```")
        return self.commit_message
