"""
Unified Retry Handler with generic decorator for handling transient failures.
"""

import asyncio
import logging
from typing import Callable, Any, TypeVar, Tuple, Type, Optional, Sequence
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Default retriable exception types
DEFAULT_RETRIABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ConnectionError,
    OSError,
    TimeoutError,
)

# Default retriable error keywords (for message-based detection)
DEFAULT_RETRIABLE_KEYWORDS: Tuple[str, ...] = (
    "rate limit",
    "timeout",
    "connection",
    "503",
    "429",
    "500",
    "502",
    "504",
)


class RetryHandler:
    """Generic handler for retrying async operations with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        retriable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        retriable_keywords: Optional[Tuple[str, ...]] = None,
        operation_name: str = "operation",
    ):
        """
        Initialize the retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff (in seconds)
            retriable_exceptions: Tuple of exception types that should trigger retry
            retriable_keywords: Tuple of keywords in error messages that indicate retriable errors
            operation_name: Name of the operation for logging purposes
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retriable_exceptions = retriable_exceptions or DEFAULT_RETRIABLE_EXCEPTIONS
        self.retriable_keywords = retriable_keywords or DEFAULT_RETRIABLE_KEYWORDS
        self.operation_name = operation_name

    def _is_retriable(self, exception: Exception) -> bool:
        """Check if an exception is retriable."""
        # Check by exception type
        if isinstance(exception, self.retriable_exceptions):
            return True

        # Check by error message keywords
        error_message = str(exception).lower()
        return any(keyword in error_message for keyword in self.retriable_keywords)

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
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries} for {self.operation_name}")
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"{self.operation_name} succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e

                if not self._is_retriable(e) or attempt == self.max_retries - 1:
                    logger.error(f"{self.operation_name} failed permanently: {e}")
                    raise

                # Calculate backoff delay
                delay = self.backoff_factor * (2 ** attempt)
                logger.warning(
                    f"{self.operation_name} failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception


def retry(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    retriable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    retriable_keywords: Optional[Tuple[str, ...]] = None,
    operation_name: Optional[str] = None,
):
    """
    Generic decorator for automatically retrying async operations.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        retriable_exceptions: Tuple of exception types that should trigger retry
        retriable_keywords: Tuple of keywords in error messages that indicate retriable errors
        operation_name: Name of the operation for logging (defaults to function name)

    Example:
        @retry(max_retries=3, backoff_factor=1.0)
        async def call_external_api():
            return await api.request()

        @retry(
            max_retries=5,
            retriable_exceptions=(ConnectionError, TimeoutError),
            operation_name="database query"
        )
        async def query_database():
            return await conn.fetch(query)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            handler = RetryHandler(
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                retriable_exceptions=retriable_exceptions,
                retriable_keywords=retriable_keywords,
                operation_name=operation_name or func.__name__,
            )
            return await handler.retry_with_backoff(func, *args, **kwargs)
        return wrapper
    return decorator


# Convenience aliases for backward compatibility and semantic clarity
def retry_on_llm_error(max_retries: int = 3, backoff_factor: float = 1.0):
    """Decorator for retrying LLM API calls."""
    return retry(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        retriable_keywords=DEFAULT_RETRIABLE_KEYWORDS,
        operation_name="LLM call",
    )


def retry_on_db_error(max_retries: int = 3, backoff_factor: float = 1.0):
    """Decorator for retrying database operations."""
    return retry(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        retriable_exceptions=DEFAULT_RETRIABLE_EXCEPTIONS,
        operation_name="DB operation",
    )


# Backward compatibility aliases for handler classes
class LLMRetryHandler(RetryHandler):
    """Handler for retrying LLM API calls (backward compatibility)."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        super().__init__(
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            retriable_keywords=DEFAULT_RETRIABLE_KEYWORDS,
            operation_name="LLM call",
        )


class DatabaseRetryHandler(RetryHandler):
    """Handler for retrying database operations (backward compatibility)."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        super().__init__(
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            retriable_exceptions=DEFAULT_RETRIABLE_EXCEPTIONS,
            operation_name="DB operation",
        )
