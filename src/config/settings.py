import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "codellama:7b")
    OLLAMA_MODEL_PATH = os.getenv("OLLAMA_MODEL_PATH", "/path/to/offline/model")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", 300))  # Increased to 5 minutes
    OLLAMA_MAX_RETRIES = int(os.getenv("OLLAMA_MAX_RETRIES", 3))  # Retry attempts
    OLLAMA_RETRY_DELAY = float(os.getenv("OLLAMA_RETRY_DELAY", 2))  # Initial retry delay
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.3))
    DEFAULT_BRANCH = os.getenv("GIT_DEFAULT_BRANCH", "main")
