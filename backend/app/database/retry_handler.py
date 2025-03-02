# app/database/retry.py
"""
Retry logic for database operations.
Implements timeout and retry mechanisms for database connections and operations.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Type, TypeVar, cast

import sqlalchemy.exc
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

# Configure default retry parameters
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 0.5  # Initial delay in seconds
DEFAULT_MAX_DELAY = 5  # Maximum delay in seconds
DEFAULT_BACKOFF_FACTOR = 2  # Exponential backoff multiplier
DEFAULT_TIMEOUT = 10  # Default operation timeout in seconds

# Define retriable exceptions
RETRIABLE_EXCEPTIONS = (
    sqlalchemy.exc.OperationalError,  # Connection issues, deadlocks
    sqlalchemy.exc.IntegrityError,  # Constraint violations
    sqlalchemy.exc.DBAPIError,  # Database API errors
)

NON_RETRIABLE_EXCEPTIONS = (
    sqlalchemy.exc.ProgrammingError,  # SQL syntax errors
    sqlalchemy.exc.DataError,  # Invalid data format
)


class DatabaseTimeoutError(Exception):
    """Raised when a database operation times out."""
    pass


class MaxRetriesExceededError(Exception):
    """Raised when maximum retries have been exceeded."""
    pass


def retry_database_operation(
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_RETRY_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    retriable_exceptions: tuple = RETRIABLE_EXCEPTIONS,
) -> Callable[[F], F]:
    """
    Decorator to retry database operations with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor by which the delay increases
        retriable_exceptions: Tuple of exceptions that should trigger a retry

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            delay = initial_delay

            # Try the operation with retries
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retriable_exceptions as e:
                    last_exception = e
                    
                    # Don't sleep on the last attempt
                    if attempt < max_retries:
                        # Log the retry attempt
                        logger.warning(
                            f"Database operation failed (attempt {attempt+1}/{max_retries+1}): {str(e)}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        
                        # Sleep with exponential backoff
                        time.sleep(delay)
                        
                        # Increase delay for next attempt, but not beyond max_delay
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        # Log the final failure
                        logger.error(
                            f"Database operation failed after {max_retries+1} attempts: {str(e)}"
                        )
                except NON_RETRIABLE_EXCEPTIONS as e:
                    # For non-retriable exceptions, log and re-raise immediately
                    logger.error(f"Non-retriable database error: {str(e)}")
                    raise

            # If we've exhausted all retries, raise the last exception
            if last_exception:
                raise MaxRetriesExceededError(f"Maximum retries exceeded: {str(last_exception)}") from last_exception
            
            # This shouldn't happen, but just in case
            raise RuntimeError("Unexpected error in retry logic")
            
        return cast(F, wrapper)
    return decorator


def with_timeout(timeout: float = DEFAULT_TIMEOUT) -> Callable[[F], F]:
    """
    Decorator to add timeout to database operations.

    Args:
        timeout: Maximum time in seconds to wait for the operation to complete

    Returns:
        Decorated function with timeout logic
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            
            def is_timed_out() -> bool:
                return time.time() - start_time > timeout
            
            # Add timeout context if the first argument is a Session
            if args and isinstance(args[0], Session):
                session = args[0]
                # Set execution timeout if supported by dialect
                if hasattr(session, 'execute'):
                    # For PostgreSQL, we can set statement timeout
                    session.execute(f"SET statement_timeout = {int(timeout * 1000)}")
            
            try:
                result = func(*args, **kwargs)
                
                if is_timed_out():
                    logger.warning(
                        f"Database operation completed but exceeded timeout of {timeout} seconds"
                    )
                    
                return result
            except Exception as e:
                if is_timed_out():
                    raise DatabaseTimeoutError(
                        f"Database operation timed out after {timeout} seconds"
                    ) from e
                raise
            
        return cast(F, wrapper)
    return decorator


def safe_db_operation(
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: float = DEFAULT_TIMEOUT
) -> Callable[[F], F]:
    """
    Combined decorator to add both retry and timeout logic to database operations.

    Args:
        max_retries: Maximum number of retry attempts
        timeout: Maximum time in seconds to wait for the operation to complete

    Returns:
        Decorated function with retry and timeout logic
    """
    def decorator(func: F) -> F:
        # Apply both decorators
        timed_func = with_timeout(timeout)(func)
        retried_func = retry_database_operation(max_retries=max_retries)(timed_func)
        return cast(F, retried_func)
    
    return decorator