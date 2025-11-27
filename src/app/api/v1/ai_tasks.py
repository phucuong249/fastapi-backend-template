"""
AI task processing endpoints (LLM, STT, TTS, Image, Video).
"""

import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from src.app.core.dependencies import check_tier, get_current_active_user
from src.app.db.models import AITask, User
from src.app.db.session import get_session
from src.app.schemas.ai_task import (
    AITaskCreate,
    AITaskResponse,
    AITaskStatusResponse,
    ImageGenerationRequest,
    LLMRequest,
    STTRequest,
    TTSRequest,
    VideoDetectionRequest,
)
from src.app.services.celery_app import (
    process_image_task,
    process_llm_task,
    process_video_task,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["AI Tasks"])


@router.post("/llm", response_model=AITaskResponse)
async def create_llm_task(
    request: LLMRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AITask:
    """
    Create a new LLM text generation task.
    
    Args:
        request: LLM generation request
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Created AI task
    """
    # Check user tier for premium features
    if request.max_tokens > 1000:
        tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
        user_tier_level = tier_hierarchy.get(current_user.tier, 0)
        required_tier_level = tier_hierarchy.get("pro", 0)
        
        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This feature requires pro tier or higher"
            )
    
    # Create task record
    task = AITask(
        user_id=current_user.id,
        task_type="llm",
        input_data=json.dumps(request.dict()),
        status="pending",
    )
    
    session.add(task)
    await session.commit()
    await session.refresh(task)
    
    # Submit to Celery
    celery_task = process_llm_task.delay(
        task_id=task.id,
        prompt=request.prompt,
        model=request.model,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )
    
    # Update task with Celery ID
    task.celery_task_id = celery_task.id
    session.add(task)
    await session.commit()
    
    logger.info(f"LLM task created: {task.id} (Celery: {celery_task.id})")
    
    return task


@router.post("/image", response_model=AITaskResponse)
async def create_image_task(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AITask:
    """
    Create a new image generation task.
    
    Args:
        request: Image generation request
        current_user: Current authenticated user (pro tier or higher)
        session: Database session
        
    Returns:
        Created AI task
    """
    # Check user tier for image generation
    tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
    user_tier_level = tier_hierarchy.get(current_user.tier, 0)
    required_tier_level = tier_hierarchy.get("pro", 0)
    
    if user_tier_level < required_tier_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Image generation requires pro tier or higher"
        )
    
    # Create task record
    task = AITask(
        user_id=current_user.id,
        task_type="image",
        input_data=json.dumps(request.dict()),
        status="pending",
    )
    
    session.add(task)
    await session.commit()
    await session.refresh(task)
    
    # Submit to Celery
    celery_task = process_image_task.delay(
        task_id=task.id,
        prompt=request.prompt,
        size=request.size,
        n=request.n,
    )
    
    # Update task with Celery ID
    task.celery_task_id = celery_task.id
    session.add(task)
    await session.commit()
    
    logger.info(f"Image generation task created: {task.id} (Celery: {celery_task.id})")
    
    return task


@router.post("/video", response_model=AITaskResponse)
async def create_video_task(
    request: VideoDetectionRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AITask:
    """
    Create a new video detection task.
    
    Args:
        request: Video detection request
        current_user: Current authenticated user (enterprise tier)
        session: Database session
        
    Returns:
        Created AI task
    """
    # Check user tier for video detection
    tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
    user_tier_level = tier_hierarchy.get(current_user.tier, 0)
    required_tier_level = tier_hierarchy.get("enterprise", 0)
    
    if user_tier_level < required_tier_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Video detection requires enterprise tier or higher"
        )
    
    # Create task record
    task = AITask(
        user_id=current_user.id,
        task_type="video",
        input_data=json.dumps(request.dict()),
        status="pending",
    )
    
    session.add(task)
    await session.commit()
    await session.refresh(task)
    
    # Submit to Celery
    celery_task = process_video_task.delay(
        task_id=task.id,
        video_url=request.video_url,
        detection_type=request.detection_type,
    )
    
    # Update task with Celery ID
    task.celery_task_id = celery_task.id
    session.add(task)
    await session.commit()
    
    logger.info(f"Video detection task created: {task.id} (Celery: {celery_task.id})")
    
    return task


@router.get("/tasks/{task_id}", response_model=AITaskStatusResponse)
async def get_task_status(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AITaskStatusResponse:
    """
    Get status of an AI task.
    
    Args:
        task_id: Task ID
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Task status and results
        
    Raises:
        HTTPException: If task not found or unauthorized
    """
    
    result = await session.execute(
        select(AITask).where(AITask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Check authorization
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this task",
        )
    
    # Get Celery task status
    from src.app.services.celery_app import celery_app
    
    celery_task = celery_app.AsyncResult(task.celery_task_id)
    
    # Calculate progress
    progress = 0.0
    if celery_task.state == "PENDING":
        progress = 0.0
    elif celery_task.state == "PROGRESS":
        progress = celery_task.info.get("progress", 0.0)
    elif celery_task.state == "SUCCESS":
        progress = 100.0
    
    output_data = None
    if task.output_data:
        output_data = json.loads(task.output_data)
    
    return AITaskStatusResponse(
        id=task.id,
        task_type=task.task_type,
        status=task.status,
        progress=progress,
        output_data=output_data,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


@router.get("/tasks", response_model=List[AITaskResponse])
async def list_user_tasks(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> List[AITask]:
    """
    List all tasks for current user.
    
    Args:
        skip: Number of tasks to skip
        limit: Maximum number of tasks to return
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        List of user's tasks
    """
    
    result = await session.execute(
        select(AITask)
        .where(AITask.user_id == current_user.id)
        .order_by(AITask.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    return result.scalars().all()
