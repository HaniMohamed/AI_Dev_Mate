# src/services/file_service.py
import os
from typing import List
from src.core.exceptions import FileServiceError

class FileService:
    @staticmethod
    def list_python_files(path: str) -> List[str]:
        """List all Python files in the given path."""
        if not os.path.exists(path):
            raise FileServiceError(f"Path does not exist: {path}")
        if not os.path.isdir(path):
            raise FileServiceError(f"Path is not a directory: {path}")
        
        files = []
        try:
            for root, _, filenames in os.walk(path):
                for f in filenames:
                    if f.endswith(".py"):
                        files.append(os.path.join(root, f))
        except PermissionError as e:
            raise FileServiceError(f"Permission denied accessing path {path}: {e}")
        return files

    @staticmethod
    def read_file(path: str) -> str:
        """Read file content with proper error handling."""
        if not os.path.exists(path):
            raise FileServiceError(f"File does not exist: {path}")
        if not os.path.isfile(path):
            raise FileServiceError(f"Path is not a file: {path}")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError as e:
            raise FileServiceError(f"Could not decode file {path} as UTF-8: {e}")
        except PermissionError as e:
            raise FileServiceError(f"Permission denied reading file {path}: {e}")
        except Exception as e:
            raise FileServiceError(f"Unexpected error reading file {path}: {e}")
    
    @staticmethod
    def file_exists(path: str) -> bool:
        """Check if a file exists."""
        return os.path.isfile(path)
    
    @staticmethod
    def dir_exists(path: str) -> bool:
        """Check if a directory exists."""
        return os.path.isdir(path)
    
    @staticmethod
    def get_file_size(path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(path)
        except OSError as e:
            raise FileServiceError(f"Could not get size of file {path}: {e}")
