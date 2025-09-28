from config.settings import Settings
# Assuming you have an Ollama Python package
# If not, keep the stub and replace later with real API

class OllamaService:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or Settings.OLLAMA_MODEL
        self.model_path = Settings.OLLAMA_MODEL_PATH
        # TODO: Load offline model here using Ollama API

    def run_prompt(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        max_tokens = max_tokens or Settings.MAX_TOKENS
        temperature = temperature or Settings.TEMPERATURE
        # Placeholder for actual Ollama call
        return f"[{self.model_name} response | max_tokens={max_tokens}, temp={temperature}]: {prompt[:200]}..."
