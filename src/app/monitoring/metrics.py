"""
Prometheus metrics for application monitoring.

Provides metrics collection for requests, database operations, and business logic.
"""

from typing import Optional

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary
except ImportError:
    # Fallback if prometheus_client is not installed
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self


# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_request_size_bytes = Summary(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
)

http_response_size_bytes = Summary(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
)

# Database Metrics
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
)

db_queries_total = Counter(
    "db_queries_total",
    "Total database queries",
    ["operation", "table", "status"],
)

db_connection_pool_size = Gauge(
    "db_connection_pool_size",
    "Database connection pool size",
)

db_connection_pool_available = Gauge(
    "db_connection_pool_available",
    "Available connections in pool",
)

# Cache Metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_name"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_name"],
)

cache_operations_duration_seconds = Histogram(
    "cache_operations_duration_seconds",
    "Cache operation duration in seconds",
    ["operation", "cache_name"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1),
)

# Task Queue Metrics
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"],
)

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"],
    buckets=(1, 5, 10, 30, 60, 300, 600, 1800),
)

celery_queue_size = Gauge(
    "celery_queue_size",
    "Celery queue size",
    ["queue_name"],
)

# Authentication Metrics
auth_attempts_total = Counter(
    "auth_attempts_total",
    "Total authentication attempts",
    ["method", "status"],
)

auth_failures_total = Counter(
    "auth_failures_total",
    "Total authentication failures",
    ["reason"],
)

active_sessions = Gauge(
    "active_sessions",
    "Number of active sessions",
)

# Business Logic Metrics
ai_tasks_total = Counter(
    "ai_tasks_total",
    "Total AI tasks processed",
    ["task_type", "status"],
)

ai_task_duration_seconds = Histogram(
    "ai_task_duration_seconds",
    "AI task duration in seconds",
    ["task_type"],
    buckets=(1, 5, 10, 30, 60, 300, 600, 1800, 3600),
)

# Error Metrics
errors_total = Counter(
    "errors_total",
    "Total errors",
    ["error_type", "endpoint"],
)

exceptions_total = Counter(
    "exceptions_total",
    "Total exceptions",
    ["exception_type"],
)

# External Service Metrics
external_service_calls_total = Counter(
    "external_service_calls_total",
    "Total external service calls",
    ["service", "endpoint", "status"],
)

external_service_duration_seconds = Histogram(
    "external_service_duration_seconds",
    "External service call duration in seconds",
    ["service", "endpoint"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# System Metrics
active_connections = Gauge(
    "active_connections",
    "Number of active connections",
)

memory_usage_bytes = Gauge(
    "memory_usage_bytes",
    "Memory usage in bytes",
)

cpu_usage_percent = Gauge(
    "cpu_usage_percent",
    "CPU usage percentage",
)


class MetricsCollector:
    """Helper class for collecting metrics."""
    
    @staticmethod
    def record_http_request(
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
    ) -> None:
        """Record HTTP request metrics."""
        http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration_seconds)
        
        if request_size:
            http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)
        if response_size:
            http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)
    
    @staticmethod
    def record_db_query(
        operation: str,
        table: str,
        duration_seconds: float,
        status: str = "success",
    ) -> None:
        """Record database query metrics."""
        db_query_duration_seconds.labels(operation=operation, table=table).observe(duration_seconds)
        db_queries_total.labels(operation=operation, table=table, status=status).inc()
    
    @staticmethod
    def record_cache_operation(
        cache_name: str,
        operation: str,
        duration_seconds: float,
        hit: bool = False,
    ) -> None:
        """Record cache operation metrics."""
        if hit:
            cache_hits_total.labels(cache_name=cache_name).inc()
        else:
            cache_misses_total.labels(cache_name=cache_name).inc()
        
        cache_operations_duration_seconds.labels(operation=operation, cache_name=cache_name).observe(duration_seconds)
    
    @staticmethod
    def record_celery_task(
        task_name: str,
        status: str,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """Record Celery task metrics."""
        celery_tasks_total.labels(task_name=task_name, status=status).inc()
        
        if duration_seconds:
            celery_task_duration_seconds.labels(task_name=task_name).observe(duration_seconds)
    
    @staticmethod
    def record_auth_attempt(method: str, success: bool) -> None:
        """Record authentication attempt."""
        status = "success" if success else "failure"
        auth_attempts_total.labels(method=method, status=status).inc()
        
        if not success:
            auth_failures_total.labels(reason="invalid_credentials").inc()
    
    @staticmethod
    def record_ai_task(task_type: str, status: str, duration_seconds: Optional[float] = None) -> None:
        """Record AI task metrics."""
        ai_tasks_total.labels(task_type=task_type, status=status).inc()
        
        if duration_seconds:
            ai_task_duration_seconds.labels(task_type=task_type).observe(duration_seconds)
    
    @staticmethod
    def record_error(error_type: str, endpoint: str) -> None:
        """Record error metrics."""
        errors_total.labels(error_type=error_type, endpoint=endpoint).inc()
    
    @staticmethod
    def record_exception(exception_type: str) -> None:
        """Record exception metrics."""
        exceptions_total.labels(exception_type=exception_type).inc()
    
    @staticmethod
    def record_external_service_call(
        service: str,
        endpoint: str,
        status: str,
        duration_seconds: float,
    ) -> None:
        """Record external service call metrics."""
        external_service_calls_total.labels(service=service, endpoint=endpoint, status=status).inc()
        external_service_duration_seconds.labels(service=service, endpoint=endpoint).observe(duration_seconds)
