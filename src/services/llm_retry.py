"""
LLM Retry Handler for handling rate limits and transient failures.
"""

import asyncio
import logging
from typing import Callable, Any, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LLMRetryHandler:
    """Handler for retrying LLM API calls with exponential backoff."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        """
        Initialize the retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff (in seconds)
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    async def retry_with_backoff(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with exponential backoff retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries} for LLM call")
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"LLM call succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e
                error_message = str(e).lower()

                # Check if it's a retriable error
                is_retriable = any(
                    keyword in error_message
                    for keyword in [
                        "rate limit",
                        "timeout",
                        "connection",
                        "503",
                        "429",
                        "500",
                        "502",
                        "504",
                    ]
                )

                if not is_retriable or attempt == self.max_retries - 1:
                    logger.error(f"LLM call failed permanently: {e}")
                    raise

                # Calculate backoff delay
                delay = self.backoff_factor * (2 ** attempt)
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception


def retry_on_llm_error(max_retries: int = 3, backoff_factor: float = 1.0):
    """
    Decorator for automatically retrying LLM calls.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff

    Example:
        @retry_on_llm_error(max_retries=3)
        async def call_llm():
            return await llm.ainvoke(prompt)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            handler = LLMRetryHandler(max_retries, backoff_factor)
            return await handler.retry_with_backoff(func, *args, **kwargs)
        return wrapper
    return decorator
