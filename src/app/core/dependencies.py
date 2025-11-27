"""
FastAPI dependencies for authentication and authorization.
"""

import logging
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions import AuthenticationException, AuthorizationException
from src.app.core.security import decode_token
from src.app.db.models import User
from src.app.db.session import get_session

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        session: Database session
        
    Returns:
        Current user
        
    Raises:
        AuthenticationException: If token is invalid or user not found
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id: int = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationException("Invalid token payload")
        
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise AuthenticationException("User not found")
        
        if not user.is_active:
            raise AuthenticationException("User is inactive")
        
        return user
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise AuthenticationException(f"Authentication failed: {str(e)}")


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Current active user
        
    Raises:
        AuthenticationException: If user is not active
    """
    if not current_user.is_active:
        raise AuthenticationException("User is inactive")
    
    return current_user


async def check_permissions(
    required_scopes: List[str],
) -> callable:
    """
    Create a dependency to check if user has required scopes.
    
    Args:
        required_scopes: List of required scopes
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        """
        Check if user has required scopes.
        
        Args:
            current_user: Current user
            session: Database session
            
        Returns:
            Current user if authorized
            
        Raises:
            AuthorizationException: If user lacks required scopes
        """
        
        # Fetch user roles and scopes
        result = await session.execute(
            select(User).where(User.id == current_user.id)
        )
        user = result.scalar_one()
        
        # Get all scopes from user roles
        user_scopes = set()
        for user_role in user.user_roles:
            role_scopes = user_role.role.scopes.split(",")
            user_scopes.update(scope.strip() for scope in role_scopes if scope.strip())
        
        # Check if user has required scopes
        for required_scope in required_scopes:
            if required_scope not in user_scopes and "admin:all" not in user_scopes:
                raise AuthorizationException(
                    f"Missing required scope: {required_scope}"
                )
        
        return user
    
    return permission_checker


async def check_tier(
    required_tier: str,
) -> callable:
    """
    Create a dependency to check if user has required tier.
    
    Args:
        required_tier: Required tier (free, pro, enterprise)
        
    Returns:
        Dependency function
    """
    tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
    
    async def tier_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """
        Check if user has required tier.
        
        Args:
            current_user: Current user
            
        Returns:
            Current user if authorized
            
        Raises:
            AuthorizationException: If user tier is insufficient
        """
        user_tier_level = tier_hierarchy.get(current_user.tier, 0)
        required_tier_level = tier_hierarchy.get(required_tier, 0)
        
        if user_tier_level < required_tier_level:
            raise AuthorizationException(
                f"This feature requires {required_tier} tier or higher"
            )
        
        return current_user
    
    return tier_checker
