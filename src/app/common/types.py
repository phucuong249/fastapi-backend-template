"""
Custom type definitions for the application.

Provides type aliases and custom types for better type safety and code clarity.
"""

from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

# Generic type variables
T = TypeVar("T")
U = TypeVar("U")

# Common type aliases
JSONData = Dict[str, Any]
JSONList = List[Dict[str, Any]]
QueryParams = Dict[str, Any]
Headers = Dict[str, str]
Metadata = Dict[str, Any]

# Numeric types
NumericValue = Union[int, float]
PositiveInt = int  # Should be validated
PositiveFloat = float  # Should be validated

# String types
Email = str  # Should be validated
URL = str  # Should be validated
UUID = str  # Should be validated
Timestamp = int  # Unix timestamp in milliseconds

# Callback types
AsyncCallback = Callable[..., Any]
SyncCallback = Callable[..., Any]

# Response types
APIResponse = Dict[str, Any]
PaginatedResponse = Dict[str, Any]

# Error types
ErrorDetail = Dict[str, Union[str, int]]
ValidationErrorDetail = Dict[str, List[str]]

# Model types
ModelID = int
UserID = int
TaskID = int
RoleID = int

# Service types
ServiceResult = Union[T, None]
ServiceError = Optional[str]

# Cache types
CacheKey = str
CacheValue = Any
CacheTTL = int  # Time to live in seconds

# Pagination types
PageNumber = int
PageSize = int
TotalCount = int
Offset = int
Limit = int

# Filter types
FilterValue = Union[str, int, float, bool, List[Any]]
FilterOperator = str  # "eq", "ne", "gt", "lt", "gte", "lte", "in", "contains"
FilterCondition = Dict[str, Union[str, FilterValue]]

# Sort types
SortField = str
SortDirection = str  # "asc" or "desc"
SortSpec = Dict[str, SortDirection]

# Rate limit types
RateLimitKey = str
RateLimitValue = int
RateLimitWindow = int  # Time window in seconds

# Task types
TaskInput = Dict[str, Any]
TaskOutput = Dict[str, Any]
TaskProgress = float  # 0.0 to 100.0

# Authentication types
Token = str
RefreshToken = str
AccessToken = str
APIKey = str
HashedPassword = str

# Configuration types
ConfigValue = Union[str, int, float, bool, List[Any], Dict[str, Any]]
ConfigDict = Dict[str, ConfigValue]

# Logging types
LogMessage = str
LogContext = Dict[str, Any]
LogLevel = str  # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"

# Metric types
MetricName = str
MetricValue = Union[int, float]
MetricLabels = Dict[str, str]

# Tracing types
TraceID = str
SpanID = str
TraceContext = Dict[str, str]

# Health check types
HealthStatus = str  # "healthy", "degraded", "unhealthy"
HealthCheck = Dict[str, Union[str, Dict[str, Any]]]

# Webhook types
WebhookURL = str
WebhookPayload = Dict[str, Any]
WebhookEvent = str

# File types
FilePath = str
FileSize = int  # in bytes
FileHash = str  # SHA256 hash
MimeType = str

# Search types
SearchQuery = str
SearchResults = List[Dict[str, Any]]
SearchMetadata = Dict[str, Any]

# Batch types
BatchID = str
BatchSize = int
BatchStatus = str  # "pending", "processing", "completed", "failed"
