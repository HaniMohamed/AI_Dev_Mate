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
