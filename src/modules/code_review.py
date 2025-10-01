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

    def set_review_params(self, base_branch: str = None, target_branch: str = None, 
                         max_files: int = None, fast_mode: bool = False):
        """Set review parameters for branch comparison."""
        self.base_branch = base_branch or "HEAD~1"  # Default to previous commit
        self.target_branch = target_branch
        self.max_files = max_files or 50  # Default to 50 files
        self.fast_mode = fast_mode

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
            
            # Get optimized diff - exclude binary files and limit to important files
            exclude_patterns = [
                "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico",  # Images
                "*.mp4", "*.avi", "*.mov", "*.wmv", "*.flv",  # Videos
                "*.mp3", "*.wav", "*.flac", "*.aac",  # Audio
                "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx",  # Documents
                "*.zip", "*.tar", "*.gz", "*.rar",  # Archives
                "*.json", "*.xml", "*.yaml", "*.yml",  # Config files (often large)
                "*.lock", "*.log", "*.tmp", "*.cache"  # Temporary files
            ]
            
            diff = GitService.get_branch_diff(
                self.base_branch, 
                self.target_branch, 
                self.repo_path,
                exclude_patterns=exclude_patterns,
                max_files=self.max_files
            )
            
            if not diff.strip():
                aidm_console.print_warning("No differences found between branches.")
                self.review = "No differences found between branches to review."
            else:
                aidm_console.print_info("Conducting aggressive code review...")
                
                # Check diff size and chunk if necessary
                diff_size = len(diff)
                aidm_console.print_info(f"Diff size: {diff_size:,} characters")
                
                if diff_size > 50000 or self.fast_mode:  # If diff is large or fast mode enabled
                    if self.fast_mode:
                        aidm_console.print_info(f"Fast mode enabled. Smart chunking for rapid analysis...")
                    else:
                        aidm_console.print_warning(f"Large diff detected ({diff_size:,} chars). Smart chunking for faster analysis...")
                    self.review = self._smart_chunked_review(diff, index_data)
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

    def _smart_chunked_review(self, diff: str, index_data: dict) -> str:
        """Review large diffs using smart chunking and parallel processing."""
        import concurrent.futures
        import threading
        
        # Split diff into smart chunks (group related files)
        chunks = self._create_smart_chunks(diff)
        total_chunks = len(chunks)
        
        aidm_console.print_info(f"Created {total_chunks} smart chunks for analysis")
        
        reviews = []
        lock = threading.Lock()
        
        def process_chunk(chunk_data):
            """Process a single chunk and return review."""
            chunk_idx, chunk_content = chunk_data
            if len(chunk_content.strip()) == 0:
                return None
                
            # Create a shorter, focused prompt for faster responses
            review_prompt = self._create_fast_review_prompt(chunk_content, index_data)
            chunk_review = self.ollama.run_prompt(review_prompt)
            
            if chunk_review and not chunk_review.startswith("[ollama"):
                return f"## Chunk {chunk_idx+1} Review\n{chunk_review}"
            return None
        
        # Process chunks in parallel (limit to 4 concurrent requests)
        with aidm_console.create_progress("Generating parallel reviews") as progress:
            task = progress.add_task("Analyzing chunks in parallel...", total=total_chunks)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all chunks for processing
                future_to_chunk = {
                    executor.submit(process_chunk, (i, chunk)): i 
                    for i, chunk in enumerate(chunks)
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_chunk):
                    chunk_idx = future_to_chunk[future]
                    try:
                        result = future.result()
                        if result:
                            reviews.append(result)
                    except Exception as e:
                        aidm_console.print_warning(f"Chunk {chunk_idx+1} failed: {e}")
                    
                    progress.update(task, completed=chunk_idx+1)
        
        # Combine all reviews
        if reviews:
            combined_review = f"# Fast Code Review ({total_chunks} chunks analyzed)\n\n"
            combined_review += "\n\n".join(reviews)
            combined_review += f"\n\n## Summary\nAnalyzed {total_chunks} chunks in parallel. Focus on critical issues above."
            return combined_review
        else:
            return "Failed to generate reviews for any chunks."

    def _create_smart_chunks(self, diff: str) -> list:
        """Create smart chunks by grouping related files together."""
        file_chunks = self._split_diff_by_files(diff)
        
        # Group files by directory/type for better context
        smart_chunks = []
        current_chunk = []
        current_size = 0
        max_chunk_size = 30000  # Target chunk size
        
        for file_chunk in file_chunks:
            chunk_size = len(file_chunk)
            
            # If adding this chunk would exceed size limit, start a new chunk
            if current_size + chunk_size > max_chunk_size and current_chunk:
                smart_chunks.append('\n'.join(current_chunk))
                current_chunk = [file_chunk]
                current_size = chunk_size
            else:
                current_chunk.append(file_chunk)
                current_size += chunk_size
        
        # Add the last chunk
        if current_chunk:
            smart_chunks.append('\n'.join(current_chunk))
        
        return smart_chunks

    def _create_fast_review_prompt(self, diff_chunk: str, project_context: dict = None) -> str:
        """Create a fast, focused review prompt for quick analysis."""
        context_info = ""
        if project_context:
            languages = project_context.get('summary', {}).get('languages', {})
            context_info = f"Project languages: {languages}\n"
        
        prompt = f"""Quick code review - focus on CRITICAL issues only:

{context_info}

REVIEW THIS CODE CHANGES (be concise, max 200 words):
{diff_chunk}

Find ONLY:
1. **SECURITY**: SQL injection, XSS, auth bypass, data leaks
2. **CRITICAL BUGS**: Null pointers, crashes, logic errors
3. **PERFORMANCE**: Memory leaks, infinite loops, N+1 queries

Format: **ISSUE**: Brief description | **FIX**: Quick solution

Be direct and brief!"""
        
        return prompt

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
