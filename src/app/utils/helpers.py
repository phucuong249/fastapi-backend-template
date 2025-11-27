"""
Helper functions for common operations.

Provides utility functions for data manipulation, formatting, and validation.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, TypeVar

T = TypeVar("T")


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length: Token length in bytes
        
    Returns:
        Hex-encoded random token
    """
    return secrets.token_hex(length)


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """
    Hash a string value.
    
    Args:
        value: String to hash
        algorithm: Hashing algorithm (sha256, sha512, etc.)
        
    Returns:
        Hex-encoded hash
    """
    return hashlib.new(algorithm, value.encode()).hexdigest()


def get_current_timestamp() -> int:
    """Get current Unix timestamp in milliseconds."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_current_datetime() -> datetime:
    """Get current datetime in UTC."""
    return datetime.now(timezone.utc)


def timestamp_to_datetime(timestamp_ms: int) -> datetime:
    """
    Convert Unix timestamp (milliseconds) to datetime.
    
    Args:
        timestamp_ms: Unix timestamp in milliseconds
        
    Returns:
        Datetime object in UTC
    """
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp (milliseconds).
    
    Args:
        dt: Datetime object
        
    Returns:
        Unix timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)


def get_future_timestamp(days: int = 0, hours: int = 0, minutes: int = 0) -> int:
    """
    Get future Unix timestamp.
    
    Args:
        days: Number of days in future
        hours: Number of hours in future
        minutes: Number of minutes in future
        
    Returns:
        Unix timestamp in milliseconds
    """
    future = get_current_datetime() + timedelta(days=days, hours=hours, minutes=minutes)
    return datetime_to_timestamp(future)


def is_expired(timestamp_ms: int) -> bool:
    """
    Check if a timestamp has expired.
    
    Args:
        timestamp_ms: Unix timestamp in milliseconds
        
    Returns:
        True if timestamp is in the past
    """
    return timestamp_ms < get_current_timestamp()


def paginate(
    items: List[T],
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        Dictionary with paginated data and metadata
    """
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "data": items[start:end],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
        },
    }


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items: List[tuple] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary (later dicts override earlier ones)
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def deep_merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        update: Dictionary to merge into base
        
    Returns:
        Deep merged dictionary
    """
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def filter_dict(d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """
    Filter dictionary to include only specified keys.
    
    Args:
        d: Dictionary to filter
        keys: Keys to include
        
    Returns:
        Filtered dictionary
    """
    return {k: v for k, v in d.items() if k in keys}


def exclude_dict(d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """
    Filter dictionary to exclude specified keys.
    
    Args:
        d: Dictionary to filter
        keys: Keys to exclude
        
    Returns:
        Filtered dictionary
    """
    return {k: v for k, v in d.items() if k not in keys}


def truncate_string(value: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to maximum length.
    
    Args:
        value: String to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated
        
    Returns:
        Truncated string
    """
    if len(value) <= max_length:
        return value
    return value[:max_length - len(suffix)] + suffix


def sanitize_string(value: str) -> str:
    """
    Sanitize a string by removing special characters.
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string
    """
    return "".join(c for c in value if c.isalnum() or c in ("-", "_", " "))


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split a list into chunks.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def deduplicate_list(items: List[T]) -> List[T]:
    """
    Remove duplicates from a list while preserving order.
    
    Args:
        items: List with potential duplicates
        
    Returns:
        List with duplicates removed
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def get_nested_value(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Get a value from nested dictionary using dot notation.
    
    Args:
        d: Dictionary to search
        path: Dot-separated path (e.g., "user.profile.name")
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    keys = path.split(".")
    value = d
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return default
        else:
            return default
    return value


def set_nested_value(d: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
    """
    Set a value in nested dictionary using dot notation.
    
    Args:
        d: Dictionary to update
        path: Dot-separated path (e.g., "user.profile.name")
        value: Value to set
        
    Returns:
        Updated dictionary
    """
    keys = path.split(".")
    current = d
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
    return d


def bytes_to_human_readable(size_bytes: int) -> str:
    """
    Convert bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def seconds_to_human_readable(seconds: float) -> str:
    """
    Convert seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human-readable duration string
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.2f}h"
    else:
        days = seconds / 86400
        return f"{days:.2f}d"
