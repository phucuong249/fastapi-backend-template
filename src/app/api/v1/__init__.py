"""
API v1 router - combines all endpoint routers.
"""

from fastapi import APIRouter

from src.app.api.v1.auth import router as auth_router
from src.app.api.v1.ai_tasks import router as ai_tasks_router

router = APIRouter()

# Include all routers
router.include_router(auth_router)
router.include_router(ai_tasks_router)
