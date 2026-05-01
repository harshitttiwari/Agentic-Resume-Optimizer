"""
Error handling and retry mechanisms for API calls.
Provides decorators for automatic retry with exponential backoff.
"""

import time
from functools import wraps
from typing import Callable, Any, Type, Tuple, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class RetryableError(Exception):
    """Raised when an operation can be retried."""
    pass


class NonRetryableError(Exception):
    """Raised when an operation should not be retried."""
    pass


def retry_on_rate_limit(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
) -> Callable:
    """
    Decorator to retry function calls on rate limit errors.
    
    Uses exponential backoff. Catches common rate limit indicators:
    - 429 HTTP status
    - "quota" in error message
    - "rate limit" in error message
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplication factor for delay
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    is_rate_limit = (
                        "429" in str(e) or
                        "quota" in error_msg or
                        "rate limit" in error_msg or
                        "too many requests" in error_msg
                    )
                    
                    if not is_rate_limit or attempt == max_retries:
                        logger.error(f"Final error in {func.__name__}: {e}")
                        raise
                    
                    last_exception = e
                    logger.warning(
                        f"Rate limit in {func.__name__}, "
                        f"retry {attempt + 1}/{max_retries} after {delay}s"
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
            
            raise last_exception if last_exception else Exception(
                f"Failed to execute {func.__name__} after {max_retries} retries"
            )
        
        return wrapper
    return decorator
