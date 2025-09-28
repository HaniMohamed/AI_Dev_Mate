# src/core/utils.py
# Utility functions
def chunk_text(text: str, size: int = 1000):
    """Split text into chunks of size."""
    for i in range(0, len(text), size):
        yield text[i:i+size]
