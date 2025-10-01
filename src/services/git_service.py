# src/services/git_service.py
import subprocess
import os
from typing import List, Optional
from src.core.exceptions import GitServiceError

class GitService:
    @staticmethod
    def _run_git_command(cmd: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Run a git command with proper error handling."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid UTF-8 sequences with replacement character
                cwd=cwd,
                timeout=30  # 30 second timeout
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown git error"
                raise GitServiceError(f"Git command failed: {' '.join(cmd)} - {error_msg}")
            return result
        except subprocess.TimeoutExpired:
            raise GitServiceError(f"Git command timed out: {' '.join(cmd)}")
        except FileNotFoundError:
            raise GitServiceError("Git is not installed or not in PATH")
        except Exception as e:
            raise GitServiceError(f"Unexpected error running git command: {e}")

    @staticmethod
    def is_git_repo(path: str) -> bool:
        """Check if the given path is a git repository."""
        git_dir = os.path.join(path, ".git")
        return os.path.exists(git_dir) and os.path.isdir(git_dir)

    @staticmethod
    def get_staged_diff(cwd: Optional[str] = None) -> str:
        """Get staged changes diff."""
        if cwd and not GitService.is_git_repo(cwd):
            raise GitServiceError(f"Not a git repository: {cwd}")
        
        result = GitService._run_git_command(["git", "diff", "--cached"], cwd)
        return result.stdout

    @staticmethod
    def get_recent_commits(n: int = 5, cwd: Optional[str] = None) -> List[str]:
        """Get recent commit messages."""
        if cwd and not GitService.is_git_repo(cwd):
            raise GitServiceError(f"Not a git repository: {cwd}")
        
        result = GitService._run_git_command(["git", "log", f"-n{n}", "--pretty=oneline"], cwd)
        return result.stdout.splitlines()
    
    @staticmethod
    def get_current_branch(cwd: Optional[str] = None) -> str:
        """Get current branch name."""
        if cwd and not GitService.is_git_repo(cwd):
            raise GitServiceError(f"Not a git repository: {cwd}")
        
        result = GitService._run_git_command(["git", "branch", "--show-current"], cwd)
        return result.stdout.strip()
    
    @staticmethod
    def get_remote_url(cwd: Optional[str] = None) -> str:
        """Get remote origin URL."""
        if cwd and not GitService.is_git_repo(cwd):
            raise GitServiceError(f"Not a git repository: {cwd}")
        
        try:
            result = GitService._run_git_command(["git", "remote", "get-url", "origin"], cwd)
            return result.stdout.strip()
        except GitServiceError:
            return ""
    
    @staticmethod
    def get_branch_diff(base_branch: str, target_branch: str = None, cwd: Optional[str] = None, 
                       exclude_patterns: list = None, max_files: int = None) -> str:
        """Get diff between two branches or between base branch and current changes.
        
        Args:
            base_branch: Base branch/commit to compare from
            target_branch: Target branch to compare to (None for working directory)
            cwd: Working directory
            exclude_patterns: List of file patterns to exclude (e.g., ['*.png', '*.jpg'])
            max_files: Maximum number of files to include in diff
        """
        if cwd and not GitService.is_git_repo(cwd):
            raise GitServiceError(f"Not a git repository: {cwd}")
        
        # Build git diff command
        cmd = ["git", "diff"]
        
        # Add branch comparison first
        if target_branch:
            cmd.append(f"{base_branch}..{target_branch}")
        else:
            if base_branch == "HEAD~1":
                cmd.append("HEAD~1")
            else:
                cmd.append(base_branch)
        
        # Add exclude patterns
        if exclude_patterns:
            cmd.append("--")
            for pattern in exclude_patterns:
                cmd.append(f":!{pattern}")
        
        # If max_files is specified, get file list first and limit
        if max_files:
            # Get list of changed files (without exclude patterns for file listing)
            file_cmd = ["git", "diff", "--name-only"]
            if target_branch:
                file_cmd.append(f"{base_branch}..{target_branch}")
            else:
                if base_branch == "HEAD~1":
                    file_cmd.append("HEAD~1")
                else:
                    file_cmd.append(base_branch)
            
            file_result = GitService._run_git_command(file_cmd, cwd)
            files = [f.strip() for f in file_result.stdout.split('\n') if f.strip()]
            
            if len(files) > max_files:
                # Limit to most important files (prioritize source code)
                priority_extensions = ['.dart', '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs']
                important_files = []
                other_files = []
                
                for file in files:
                    if any(file.endswith(ext) for ext in priority_extensions):
                        important_files.append(file)
                    else:
                        other_files.append(file)
                
                # Take important files first, then fill remaining slots with other files
                selected_files = important_files[:max_files]
                remaining_slots = max_files - len(selected_files)
                selected_files.extend(other_files[:remaining_slots])
                
                # Create diff for selected files only
                cmd.extend(["--"] + selected_files)
        
        result = GitService._run_git_command(cmd, cwd)
        return result.stdout
    
    @staticmethod
    def get_available_branches(cwd: Optional[str] = None) -> List[str]:
        """Get list of available branches."""
        if cwd and not GitService.is_git_repo(cwd):
            raise GitServiceError(f"Not a git repository: {cwd}")
        
        result = GitService._run_git_command(["git", "branch", "-a"], cwd)
        branches = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("*"):
                line = line[1:].strip()  # Remove current branch marker
            if line.startswith("remotes/"):
                line = line[8:]  # Remove "remotes/" prefix
            if line and not line.startswith("HEAD"):
                branches.append(line)
        
        return list(set(branches))  # Remove duplicates
    
    @staticmethod
    def branch_exists(branch_name: str, cwd: Optional[str] = None) -> bool:
        """Check if a branch exists."""
        if cwd and not GitService.is_git_repo(cwd):
            raise GitServiceError(f"Not a git repository: {cwd}")
        
        try:
            GitService._run_git_command(["git", "rev-parse", "--verify", branch_name], cwd)
            return True
        except GitServiceError:
            return False
