"""
Database models using SQLModel (SQLAlchemy + Pydantic).
"""

from datetime import datetime
from typing import List, Optional

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, String


class Role(SQLModel, table=True):
    """Role model for RBAC."""
    
    __tablename__ = "roles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)
    scopes: str = Field(
        default="",
        description="Comma-separated list of scopes (e.g., 'llm:write,image:generate')",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    
    # Relationships
    user_roles: List["UserRole"] = Relationship(back_populates="role")


class User(SQLModel, table=True):
    """User model with authentication fields."""
    
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, max_length=100)
    hashed_password: str = Field(max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True, index=True)
    is_verified: bool = Field(default=False)
    tier: str = Field(default="free", description="User tier: free, pro, enterprise")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    last_login: Optional[datetime] = Field(default=None)
    
    # Relationships
    user_roles: List["UserRole"] = Relationship(back_populates="user")
    api_keys: List["APIKey"] = Relationship(back_populates="user")


class UserRole(SQLModel, table=True):
    """Association table for User-Role many-to-many relationship."""
    
    __tablename__ = "user_roles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    role_id: int = Field(foreign_key="roles.id", index=True)
    assigned_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    
    # Relationships
    user: User = Relationship(back_populates="user_roles")
    role: Role = Relationship(back_populates="user_roles")


class APIKey(SQLModel, table=True):
    """API Key model for programmatic access."""
    
    __tablename__ = "api_keys"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    hashed_key: str = Field(max_length=255, unique=True, index=True)
    is_active: bool = Field(default=True, index=True)
    last_used: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    expires_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    user: User = Relationship(back_populates="api_keys")


class AITask(SQLModel, table=True):
    """Model for tracking AI processing tasks."""
    
    __tablename__ = "ai_tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    task_type: str = Field(
        index=True,
        description="Task type: llm, stt, tts, image, video",
    )
    celery_task_id: str = Field(unique=True, index=True, max_length=255)
    status: str = Field(
        default="pending",
        index=True,
        description="Status: pending, processing, completed, failed",
    )
    input_data: str = Field(description="JSON string of input parameters")
    output_data: Optional[str] = Field(default=None, description="JSON string of results")
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )
    completed_at: Optional[datetime] = Field(default=None)
