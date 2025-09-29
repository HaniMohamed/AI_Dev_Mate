from src.config.settings import Settings
import requests
from typing import Optional, Dict, Any


class OllamaService:
    def __init__(self, model_name: Optional[str] = None, host: Optional[str] = None, timeout: Optional[float] = None):
        self.model_name = model_name or Settings.OLLAMA_MODEL
        self.host = (host or Settings.OLLAMA_HOST).rstrip("/")
        self.timeout = timeout or Settings.OLLAMA_TIMEOUT

    def run_prompt(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Call Ollama's HTTP API to generate a completion for the given prompt.
        Uses /api/generate with streaming disabled for simplicity.
        """
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else Settings.TEMPERATURE,
            },
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        url = f"{self.host}/api/generate"
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            # The non-streaming API returns a single JSON with 'response'
            return data.get("response", "")
        except requests.Timeout:
            return "[ollama timeout]"
        except requests.RequestException as e:
            return f"[ollama error] {e}"
