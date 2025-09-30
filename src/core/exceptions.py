# src/core/exceptions.py
"""
Custom exception classes for AI Dev Mate.
"""

class AIDevMateError(Exception):
    """Base exception class for AI Dev Mate."""
    pass

class FileServiceError(AIDevMateError):
    """Raised when file operations fail."""
    pass

class GitServiceError(AIDevMateError):
    """Raised when git operations fail."""
    pass

class IndexError(AIDevMateError):
    """Raised when indexing operations fail."""
    pass

class OllamaServiceError(AIDevMateError):
    """Raised when Ollama service operations fail."""
    pass

class TaskError(AIDevMateError):
    """Raised when task execution fails."""
    pass