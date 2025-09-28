# src/services/git_service.py
import subprocess
from typing import List

class GitService:
    @staticmethod
    def get_staged_diff() -> str:
        result = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True
        )
        return result.stdout

    @staticmethod
    def get_recent_commits(n: int = 5) -> List[str]:
        result = subprocess.run(
            ["git", "log", f"-n{n}", "--pretty=oneline"],
            capture_output=True,
            text=True
        )
        return result.stdout.splitlines()
