# src/modules/code_review.py
import os
from src.core.models import BaseTask
from src.core.utils import check_and_load_index, create_aggressive_review_prompt
from src.services.ollama_service import OllamaService
from src.services.git_service import GitService
from src.utils.console import aidm_console

class CodeReviewTask(BaseTask):
    def __init__(self, ollama: OllamaService, repo_path: str = None):
        super().__init__("Code Review")
        self.ollama = ollama
        self.review = ""
        self.repo_path = repo_path
        self.base_branch = "HEAD~1"  # Compare with previous commit instead of main branch
        self.target_branch = None

    def set_review_params(self, base_branch: str = None, target_branch: str = None):
        """Set review parameters for branch comparison."""
        self.base_branch = base_branch or "HEAD~1"  # Default to previous commit
        self.target_branch = target_branch

    def run(self):
        """Run aggressive code review with beautiful output."""
        # Ask for repository path if not set
        if not self.repo_path:
            self.repo_path = aidm_console.prompt("Enter path to repository to review")
        
        aidm_console.print_header("🔍 Aggressive Code Review", f"Target: {self.repo_path}")
        
        # Check if indexed data is available
        index_data = check_and_load_index(repo_path=self.repo_path, ollama=self.ollama)
        if index_data is None:
            self.review = "Code review failed: No indexed data available. Please index the project first."
            self.completed = True
            return
        
        try:
            # Verify git repository
            if not GitService.is_git_repo(self.repo_path):
                aidm_console.print_error(f"Not a git repository: {self.repo_path}")
                self.review = f"Code review failed: {self.repo_path} is not a git repository."
                self.completed = True
                return
            
            # Check if base branch/commit exists (skip check for HEAD~1 as it's a commit reference)
            if self.base_branch != "HEAD~1" and not GitService.branch_exists(self.base_branch, self.repo_path):
                aidm_console.print_warning(f"Base branch '{self.base_branch}' not found. Available branches:")
                available_branches = GitService.get_available_branches(self.repo_path)
                for branch in available_branches[:10]:  # Show first 10 branches
                    aidm_console.print_info(f"  - {branch}")
                if len(available_branches) > 10:
                    aidm_console.print_info(f"  ... and {len(available_branches) - 10} more")
                
                self.review = f"Code review failed: Base branch '{self.base_branch}' not found."
                self.completed = True
                return
            
            # Get the diff
            comparison_desc = "previous commit" if self.base_branch == "HEAD~1" else self.base_branch
            aidm_console.print_info(f"Comparing {comparison_desc} with {'current changes' if not self.target_branch else self.target_branch}")
            
            if self.target_branch and not GitService.branch_exists(self.target_branch, self.repo_path):
                aidm_console.print_error(f"Target branch '{self.target_branch}' not found.")
                self.review = f"Code review failed: Target branch '{self.target_branch}' not found."
                self.completed = True
                return
            
            diff = GitService.get_branch_diff(self.base_branch, self.target_branch, self.repo_path)
            
            if not diff.strip():
                aidm_console.print_warning("No differences found between branches.")
                self.review = "No differences found between branches to review."
            else:
                aidm_console.print_info("Conducting aggressive code review...")
                
                # Show the diff with syntax highlighting
                aidm_console.print_primary("Code Changes:")
                aidm_console.print_code_syntax(diff, "diff")
                
                # Generate aggressive review using indexed context
                with aidm_console.create_progress("Generating aggressive review") as progress:
                    task = progress.add_task("Analyzing code for issues...", total=100)
                    
                    # Create aggressive review prompt
                    review_prompt = create_aggressive_review_prompt(diff, index_data)
                    self.review = self.ollama.run_prompt(review_prompt)
                    progress.update(task, completed=100)
                
                aidm_console.print_success("Aggressive code review completed!")
                
        except Exception as e:
            aidm_console.print_error(f"Code review failed: {e}")
            self.review = f"Code review failed: {e}"
        
        self.completed = True

    def summarize(self) -> str:
        """Return review summary with beautiful formatting."""
        if self.review:
            aidm_console.print_separator()
            aidm_console.print_header("📋 Aggressive Review Results", "Comprehensive code analysis")
            aidm_console.print_markdown(self.review)
        return self.review
