# src/utils/decorators.py
import time
import functools
from src.utils.logger import logger

def timeit(func):
    """Decorator to measure execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"Task {func.__name__} executed in {elapsed:.2f}s")
        return result
    return wrapper
