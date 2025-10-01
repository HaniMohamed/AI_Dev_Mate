from src.config.settings import Settings
import requests
import time
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
                # Performance optimizations for faster generation
                "num_predict": max_tokens if max_tokens is not None else Settings.MAX_TOKENS,
                "num_ctx": 4096,  # Context window size
                "num_thread": 4,  # Use 4 threads for faster processing
                "num_gpu": 1,  # Use GPU if available
                "repeat_penalty": 1.1,  # Slight penalty for repetition
                "top_k": 40,  # Limit vocabulary for faster generation
                "top_p": 0.9,  # Nucleus sampling for better quality
                "repeat_last_n": 64,  # Look back 64 tokens for repetition
                "num_batch": 512,  # Batch size for processing
                "low_vram": False,  # Use full VRAM if available
                "f16_kv": True,  # Use 16-bit precision for key-value cache
                "use_mmap": True,  # Use memory mapping for faster loading
                "use_mlock": True,  # Lock memory to prevent swapping
                "n_gpu_layers": -1,  # Use all GPU layers
                "main_gpu": 0,  # Use first GPU
                "stop": ["</s>", "\n\n"],  # Stop tokens
            },
        }

        url = f"{self.host}/api/generate"
        
        # Retry logic for better reliability
        max_retries = Settings.OLLAMA_MAX_RETRIES
        retry_delay = Settings.OLLAMA_RETRY_DELAY
        
        for attempt in range(max_retries):
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                # The non-streaming API returns a single JSON with 'response'
                return data.get("response", "")
            except requests.Timeout:
                if attempt < max_retries - 1:
                    print(f"Ollama timeout (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                return "[ollama timeout]"
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"Ollama error (attempt {attempt + 1}/{max_retries}): {e}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                return f"[ollama error] {e}"
        
        return "[ollama error] Max retries exceeded"
