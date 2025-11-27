"""
Enumeration classes for the application.

Defines all enum types used across the application for type safety and consistency.
"""

from enum import Enum


class UserTier(str, Enum):
    """User subscription tiers."""
    
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserRole(str, Enum):
    """User roles for RBAC."""
    
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class TaskStatus(str, Enum):
    """AI task processing status."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Types of AI tasks."""
    
    LLM = "llm"
    STT = "stt"
    TTS = "tts"
    IMAGE = "image"
    VIDEO = "video"


class LLMProvider(str, Enum):
    """LLM service providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LLAMA = "llama"
    HUGGINGFACE = "huggingface"


class ImageProvider(str, Enum):
    """Image generation service providers."""
    
    OPENAI = "openai"
    STABLE_DIFFUSION = "stable_diffusion"
    MIDJOURNEY = "midjourney"


class DetectionType(str, Enum):
    """Types of video/image detection."""
    
    OBJECT = "object"
    POSE = "pose"
    FACE = "face"
    HAND = "hand"
    CUSTOM = "custom"


class ErrorCode(str, Enum):
    """Application error codes."""
    
    # Authentication errors
    AUTH_INVALID_CREDENTIALS = "auth_invalid_credentials"
    AUTH_TOKEN_EXPIRED = "auth_token_expired"
    AUTH_TOKEN_INVALID = "auth_token_invalid"
    AUTH_USER_INACTIVE = "auth_user_inactive"
    
    # Authorization errors
    AUTHZ_INSUFFICIENT_PERMISSIONS = "authz_insufficient_permissions"
    AUTHZ_INSUFFICIENT_TIER = "authz_insufficient_tier"
    
    # Validation errors
    VALIDATION_ERROR = "validation_error"
    VALIDATION_INVALID_EMAIL = "validation_invalid_email"
    VALIDATION_WEAK_PASSWORD = "validation_weak_password"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "resource_not_found"
    RESOURCE_ALREADY_EXISTS = "resource_already_exists"
    RESOURCE_CONFLICT = "resource_conflict"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Server errors
    INTERNAL_SERVER_ERROR = "internal_server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    EXTERNAL_SERVICE_ERROR = "external_service_error"


class LogLevel(str, Enum):
    """Logging levels."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Application environments."""
    
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class CacheType(str, Enum):
    """Cache types."""
    
    MEMORY = "memory"
    REDIS = "redis"
    NONE = "none"


class SortOrder(str, Enum):
    """Sort order for list operations."""
    
    ASC = "asc"
    DESC = "desc"
