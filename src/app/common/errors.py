"""
Error handling utilities and custom error classes.

Provides structured error handling and error response formatting.
"""

from typing import Any, Dict, List, Optional

from src.app.common.enums import ErrorCode


class APIError(Exception):
    """Base API error class."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(APIError):
    """Validation error."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, List[str]]] = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=details or {},
        )


class AuthenticationError(APIError):
    """Authentication error."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: ErrorCode = ErrorCode.AUTH_INVALID_CREDENTIALS,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
        )


class AuthorizationError(APIError):
    """Authorization error."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        error_code: ErrorCode = ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
        )


class NotFoundError(APIError):
    """Resource not found error."""
    
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            message=f"{resource} not found",
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
        )


class ConflictError(APIError):
    """Resource conflict error."""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_CONFLICT,
            status_code=409,
        )


class RateLimitError(APIError):
    """Rate limit exceeded error."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details,
        )


class ExternalServiceError(APIError):
    """External service error."""
    
    def __init__(
        self,
        service: str,
        message: str = "External service error",
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=502,
            details={"service": service},
        )


class InternalServerError(APIError):
    """Internal server error."""
    
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            message=message,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=500,
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error."""
    
    def __init__(self, message: str = "Service unavailable"):
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=503,
        )


class InvalidEmailError(ValidationError):
    """Invalid email error."""
    
    def __init__(self, email: str):
        super().__init__(
            message="Invalid email address",
            details={"email": [f"'{email}' is not a valid email"]},
        )


class WeakPasswordError(ValidationError):
    """Weak password error."""
    
    def __init__(self, reason: str = "Password is too weak"):
        super().__init__(
            message="Password does not meet requirements",
            details={"password": [reason]},
        )


class DuplicateResourceError(ConflictError):
    """Duplicate resource error."""
    
    def __init__(self, resource: str, field: str, value: str):
        super().__init__(
            message=f"{resource} with {field}='{value}' already exists"
        )


class TokenExpiredError(AuthenticationError):
    """Token expired error."""
    
    def __init__(self):
        super().__init__(
            message="Token has expired",
            error_code=ErrorCode.AUTH_TOKEN_EXPIRED,
        )


class InvalidTokenError(AuthenticationError):
    """Invalid token error."""
    
    def __init__(self):
        super().__init__(
            message="Invalid token",
            error_code=ErrorCode.AUTH_TOKEN_INVALID,
        )


class InsufficientTierError(AuthorizationError):
    """Insufficient user tier error."""
    
    def __init__(self, required_tier: str, current_tier: str):
        super().__init__(
            message=f"This feature requires {required_tier} tier or higher",
            error_code=ErrorCode.AUTHZ_INSUFFICIENT_TIER,
        )
        self.details = {
            "required_tier": required_tier,
            "current_tier": current_tier,
        }


def format_validation_errors(errors: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Format Pydantic validation errors into a dictionary.
    
    Args:
        errors: List of Pydantic validation errors
        
    Returns:
        Dictionary mapping field names to error messages
    """
    formatted = {}
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"][1:])
        if field not in formatted:
            formatted[field] = []
        formatted[field].append(error["msg"])
    return formatted
