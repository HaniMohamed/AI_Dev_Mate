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
                # Optimized for SPEED - reduced quality for faster responses
                "num_predict": min(max_tokens if max_tokens is not None else Settings.MAX_TOKENS, 2000),  # Limit response length
                "num_ctx": 4096,  # Smaller context window for speed
                "num_thread": 8,  # More threads for faster processing
                "num_gpu": 1,  # Use GPU if available
                "repeat_penalty": 1.05,  # Reduced penalty for speed
                "top_k": 20,  # Smaller vocabulary for faster generation
                "top_p": 0.8,  # Reduced sampling for speed
                "repeat_last_n": 32,  # Reduced lookback for speed
                "num_batch": 1024,  # Larger batch size for speed
                "low_vram": False,  # Use full VRAM if available
                "f16_kv": True,  # Use 16-bit precision for key-value cache
                "use_mmap": True,  # Use memory mapping for faster loading
                "use_mlock": True,  # Lock memory to prevent swapping
                "n_gpu_layers": -1,  # Use all GPU layers
                "main_gpu": 0,  # Use first GPU
                "stop": ["</s>", "\n\n\n"],  # Stop on multiple patterns for shorter responses
                "tfs_z": 1.0,  # Tail free sampling for faster generation
                "typical_p": 1.0,  # Typical sampling for speed
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
                response_text = data.get("response", "")
                
                # Debug: Log response length for troubleshooting
                if len(response_text) > 0:
                    print(f"Ollama response length: {len(response_text)} characters")
                
                return response_text
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
