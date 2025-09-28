import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "codellama")
    OLLAMA_MODEL_PATH = os.getenv("OLLAMA_MODEL_PATH", "/path/to/offline/model")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.3))
    DEFAULT_BRANCH = os.getenv("GIT_DEFAULT_BRANCH", "main")
