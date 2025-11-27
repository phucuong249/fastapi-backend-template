"""
Structured logging configuration using structlog.

Provides centralized logging setup with JSON formatting for production
and human-readable formatting for development.
"""

import logging
import sys
from typing import Any, Dict

import structlog

from src.app.core.config import settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    
    Sets up both standard logging and structlog with appropriate
    formatters based on the environment.
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.DEBUG else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding context to logs."""
    
    def __init__(self, **context: Any):
        """
        Initialize log context.
        
        Args:
            **context: Key-value pairs to add to log context
        """
        self.context = context
        self.logger = structlog.get_logger()
    
    def __enter__(self) -> "LogContext":
        """Enter context and bind values."""
        self.logger = self.logger.bind(**self.context)
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and unbind values."""
        self.logger = self.logger.unbind(*self.context.keys())


class RequestLogger:
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app: Any):
        """
        Initialize request logger middleware.
        
        Args:
            app: FastAPI application instance
        """
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        """
        Process HTTP request and log details.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract request details
        method = scope.get("method", "")
        path = scope.get("path", "")
        query_string = scope.get("query_string", b"").decode()
        
        # Log request
        self.logger.info(
            "http_request",
            method=method,
            path=path,
            query_string=query_string,
        )
        
        # Wrap send to log response
        async def send_wrapper(message: Dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                self.logger.info(
                    "http_response",
                    method=method,
                    path=path,
                    status_code=status_code,
                )
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


def log_exception(logger: structlog.BoundLogger, exc: Exception, **context: Any) -> None:
    """
    Log an exception with context.
    
    Args:
        logger: Structlog logger instance
        exc: Exception to log
        **context: Additional context to include
    """
    logger.exception(
        "exception_occurred",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        **context,
    )


def log_performance(logger: structlog.BoundLogger, operation: str, duration_ms: float, **context: Any) -> None:
    """
    Log performance metrics for an operation.
    
    Args:
        logger: Structlog logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        **context: Additional context
    """
    level = "warning" if duration_ms > 1000 else "info"
    
    logger.log(
        level,
        "performance_metric",
        operation=operation,
        duration_ms=duration_ms,
        **context,
    )


def log_database_query(logger: structlog.BoundLogger, query: str, duration_ms: float, **context: Any) -> None:
    """
    Log database query execution.
    
    Args:
        logger: Structlog logger instance
        query: SQL query
        duration_ms: Query duration in milliseconds
        **context: Additional context
    """
    level = "warning" if duration_ms > 500 else "debug"
    
    logger.log(
        level,
        "database_query",
        query=query,
        duration_ms=duration_ms,
        **context,
    )


def log_external_service_call(
    logger: structlog.BoundLogger,
    service: str,
    endpoint: str,
    duration_ms: float,
    status_code: int,
    **context: Any,
) -> None:
    """
    Log external service API call.
    
    Args:
        logger: Structlog logger instance
        service: Service name
        endpoint: API endpoint
        duration_ms: Call duration in milliseconds
        status_code: HTTP status code
        **context: Additional context
    """
    level = "warning" if status_code >= 400 or duration_ms > 5000 else "info"
    
    logger.log(
        level,
        "external_service_call",
        service=service,
        endpoint=endpoint,
        duration_ms=duration_ms,
        status_code=status_code,
        **context,
    )


def log_security_event(logger: structlog.BoundLogger, event: str, **context: Any) -> None:
    """
    Log security-related events.
    
    Args:
        logger: Structlog logger instance
        event: Security event description
        **context: Additional context
    """
    logger.warning(
        "security_event",
        event=event,
        **context,
    )


def log_audit_event(
    logger: structlog.BoundLogger,
    action: str,
    user_id: int,
    resource: str,
    **context: Any,
) -> None:
    """
    Log audit trail events.
    
    Args:
        logger: Structlog logger instance
        action: Action performed
        user_id: User ID performing action
        resource: Resource affected
        **context: Additional context
    """
    logger.info(
        "audit_event",
        action=action,
        user_id=user_id,
        resource=resource,
        **context,
    )
