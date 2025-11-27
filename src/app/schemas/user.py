"""
Pydantic schemas for User-related endpoints.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class RoleSchema(BaseModel):
    """Role schema."""
    
    id: int
    name: str
    description: Optional[str] = None
    scopes: str


class UserBase(BaseModel):
    """Base user schema."""
    
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """User creation schema."""
    
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """User update schema."""
    
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """User response schema."""
    
    id: int
    is_active: bool
    is_verified: bool
    tier: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    roles: List[RoleSchema] = []
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Login request schema."""
    
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str


class APIKeyCreate(BaseModel):
    """API Key creation schema."""
    
    name: str = Field(..., min_length=1, max_length=100)
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API Key response schema."""
    
    id: int
    name: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class APIKeyCreateResponse(APIKeyResponse):
    """API Key creation response with the actual key."""
    
    key: str  # Only returned once during creation
