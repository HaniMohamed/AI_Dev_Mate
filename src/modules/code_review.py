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
                
                # Check diff size and chunk if necessary
                diff_size = len(diff)
                aidm_console.print_info(f"Diff size: {diff_size:,} characters")
                
                if diff_size > 100000:  # If diff is larger than 100KB, chunk it
                    aidm_console.print_warning(f"Large diff detected ({diff_size:,} chars). Chunking for better analysis...")
                    self.review = self._chunked_review(diff, index_data)
                else:
                    # Show the diff with syntax highlighting for smaller diffs
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

    def _chunked_review(self, diff: str, index_data: dict) -> str:
        """Review large diffs by chunking them into manageable pieces."""
        from src.core.utils import chunk_text
        
        # Split diff into chunks by file boundaries
        chunks = self._split_diff_by_files(diff)
        total_chunks = len(chunks)
        
        aidm_console.print_info(f"Split diff into {total_chunks} file chunks for analysis")
        
        reviews = []
        
        with aidm_console.create_progress("Generating chunked review") as progress:
            task = progress.add_task("Analyzing chunks...", total=total_chunks)
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) == 0:
                    continue
                    
                aidm_console.print_info(f"Reviewing chunk {i+1}/{total_chunks} ({len(chunk):,} chars)")
                
                # Create review prompt for this chunk
                review_prompt = create_aggressive_review_prompt(chunk, index_data)
                chunk_review = self.ollama.run_prompt(review_prompt)
                
                if chunk_review and not chunk_review.startswith("[ollama"):
                    reviews.append(f"## Chunk {i+1} Review\n{chunk_review}")
                
                progress.update(task, completed=i+1)
        
        # Combine all reviews
        if reviews:
            combined_review = f"# Comprehensive Code Review ({total_chunks} chunks analyzed)\n\n"
            combined_review += "\n\n".join(reviews)
            combined_review += f"\n\n## Summary\nAnalyzed {total_chunks} file chunks. Review each section above for specific issues."
            return combined_review
        else:
            return "Failed to generate reviews for any chunks."

    def _split_diff_by_files(self, diff: str) -> list:
        """Split diff into chunks by file boundaries."""
        lines = diff.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            # Check if this is a new file diff header
            if line.startswith('diff --git'):
                # Save previous chunk if it exists
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
            
            current_chunk.append(line)
        
        # Add the last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks

    def summarize(self) -> str:
        """Return review summary with beautiful formatting."""
        if self.review:
            aidm_console.print_separator()
            aidm_console.print_header("📋 Aggressive Review Results", "Comprehensive code analysis")
            aidm_console.print_markdown(self.review)
        return self.review
