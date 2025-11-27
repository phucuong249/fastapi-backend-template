"""
Custom decorators for common patterns.

Provides decorators for timing, caching, retry logic, and validation.
"""

import asyncio
import functools
import time
from typing import Any, Awaitable, Callable, Optional, TypeVar, Union

from src.app.core.logging import get_logger
from src.app.monitoring.metrics import MetricsCollector

logger = get_logger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def timing(func: F) -> F:
    """
    Decorator to measure function execution time.
    
    Logs the duration and warns if execution time exceeds threshold.
    """
    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                "function_executed",
                function=func.__name__,
                duration_seconds=duration,
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "function_failed",
                function=func.__name__,
                duration_seconds=duration,
                error=str(e),
            )
            raise
    
    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                "async_function_executed",
                function=func.__name__,
                duration_seconds=duration,
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "async_function_failed",
                function=func.__name__,
                duration_seconds=duration,
                error=str(e),
            )
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper  # type: ignore
    return sync_wrapper  # type: ignore


def retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator to retry function on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay_seconds: Initial delay between retries
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = delay_seconds
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "function_retry",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            delay_seconds=delay,
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
            
            logger.error(
                "function_failed_all_retries",
                function=func.__name__,
                max_attempts=max_attempts,
            )
            raise last_exception or Exception("Max retries exceeded")
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = delay_seconds
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "async_function_retry",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            delay_seconds=delay,
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
            
            logger.error(
                "async_function_failed_all_retries",
                function=func.__name__,
                max_attempts=max_attempts,
            )
            raise last_exception or Exception("Max retries exceeded")
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


def cache(ttl_seconds: int = 300) -> Callable[[F], F]:
    """
    Decorator to cache function results.
    
    Args:
        ttl_seconds: Time to live for cached results
    """
    def decorator(func: F) -> F:
        cache_dict: dict = {}
        cache_time: dict = {}
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = (args, tuple(sorted(kwargs.items())))
            current_time = time.time()
            
            if cache_key in cache_dict:
                if current_time - cache_time[cache_key] < ttl_seconds:
                    logger.debug(
                        "cache_hit",
                        function=func.__name__,
                    )
                    return cache_dict[cache_key]
                else:
                    del cache_dict[cache_key]
                    del cache_time[cache_key]
            
            result = func(*args, **kwargs)
            cache_dict[cache_key] = result
            cache_time[cache_key] = current_time
            
            logger.debug(
                "cache_miss",
                function=func.__name__,
            )
            return result
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = (args, tuple(sorted(kwargs.items())))
            current_time = time.time()
            
            if cache_key in cache_dict:
                if current_time - cache_time[cache_key] < ttl_seconds:
                    logger.debug(
                        "async_cache_hit",
                        function=func.__name__,
                    )
                    return cache_dict[cache_key]
                else:
                    del cache_dict[cache_key]
                    del cache_time[cache_key]
            
            result = await func(*args, **kwargs)
            cache_dict[cache_key] = result
            cache_time[cache_key] = current_time
            
            logger.debug(
                "async_cache_miss",
                function=func.__name__,
            )
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


def validate_input(**validators: Callable[[Any], bool]) -> Callable[[F], F]:
    """
    Decorator to validate function inputs.
    
    Args:
        **validators: Mapping of parameter names to validation functions
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Validate kwargs
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    if not validator(kwargs[param_name]):
                        raise ValueError(f"Invalid value for parameter '{param_name}'")
            
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator


def handle_exceptions(
    default_return: Optional[Any] = None,
    log_error: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to handle exceptions gracefully.
    
    Args:
        default_return: Value to return if exception occurs
        log_error: Whether to log the error
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.exception(
                        "exception_in_function",
                        function=func.__name__,
                        error=str(e),
                    )
                return default_return
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.exception(
                        "exception_in_async_function",
                        function=func.__name__,
                        error=str(e),
                    )
                return default_return
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


def rate_limit(calls: int, period_seconds: int) -> Callable[[F], F]:
    """
    Decorator to rate limit function calls.
    
    Args:
        calls: Number of calls allowed
        period_seconds: Time period in seconds
    """
    def decorator(func: F) -> F:
        call_times: list = []
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = time.time()
            
            # Remove old calls outside the period
            call_times[:] = [t for t in call_times if now - t < period_seconds]
            
            if len(call_times) >= calls:
                raise RuntimeError(f"Rate limit exceeded: {calls} calls per {period_seconds}s")
            
            call_times.append(now)
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator
