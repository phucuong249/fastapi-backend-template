"""
AI task processing endpoints (LLM, STT, TTS, Image, Video).
"""

import json
import logging
from typing import Any, Callable, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.common.enums import TaskStatus, TaskType
from src.app.core.dependencies import get_current_active_user
from src.app.core.exceptions import AuthorizationException, ResourceNotFoundException, ValidationException
from src.app.db.models import AITask, User
from src.app.db.session import get_session
from src.app.schemas.ai_task import (
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
    process_stt_task,
    process_tts_task,
    process_video_task,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["AI Tasks"])


SubmitTaskCallable = Callable[[int, Dict[str, Any]], Any]
TIER_HIERARCHY = {"free": 0, "pro": 1, "enterprise": 2}


def _require_tier(user: User, required_tier: str, task_type: str, context: Dict[str, Any] | None = None) -> None:
    """
    Ensure the user has the required tier for a task.
    """
    user_level = TIER_HIERARCHY.get(user.tier, 0)
    required_level = TIER_HIERARCHY.get(required_tier, 0)

    if user_level >= required_level:
        return

    extra = {
        "event": "tier_restriction_violation",
        "user_id": user.id,
        "user_tier": user.tier,
        "required_tier": required_tier,
        "task_type": task_type,
    }
    if context:
        extra.update(context)

    logger.warning(f"User {user.id} failed tier check for {task_type}", extra=extra)
    raise AuthorizationException(f"{task_type} tasks require {required_tier} tier or higher")


async def _create_and_dispatch_task(
    *,
    task_type: TaskType,
    payload: Dict[str, Any],
    session: AsyncSession,
    current_user: User,
    submitter: SubmitTaskCallable,
) -> AITask:
    """
    Persist an AI task and enqueue it via Celery.
    """
    task = AITask(
        user_id=current_user.id,
        task_type=task_type.value,
        input_data=json.dumps(payload),
        status=TaskStatus.PENDING.value,
    )

    session.add(task)
    await session.commit()
    await session.refresh(task)

    celery_result = submitter(task.id, payload)
    task.celery_task_id = celery_result.id
    session.add(task)
    await session.commit()
    await session.refresh(task)

    logger.info(
        "%s task created: %s (Celery: %s)",
        task_type.value,
        task.id,
        task.celery_task_id,
    )
    return task


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
    if not (1 <= request.max_tokens <= 4000):
        raise ValidationException("max_tokens must be between 1 and 4000")
    
    if not (0.0 <= request.temperature <= 2.0):
        raise ValidationException("temperature must be between 0.0 and 2.0")
    
    # Check user tier for premium features
    if request.max_tokens > 1000:
        _require_tier(
            current_user,
            required_tier="pro",
            task_type="llm",
            context={"max_tokens": request.max_tokens},
        )
    
    payload = request.dict()
    return await _create_and_dispatch_task(
        task_type=TaskType.LLM,
        payload=payload,
        session=session,
        current_user=current_user,
        submitter=lambda task_id, data: process_llm_task.delay(task_id=task_id, payload=data),
    )


@router.post("/stt", response_model=AITaskResponse)
async def create_stt_task(
    request: STTRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AITask:
    """
    Create a speech-to-text task that runs locally.
    """
    if len(request.file_url) > 2000:
        raise ValidationException("file_url must be shorter than 2000 characters")
    
    _require_tier(current_user, required_tier="pro", task_type="stt")
    
    payload = request.dict()
    return await _create_and_dispatch_task(
        task_type=TaskType.STT,
        payload=payload,
        session=session,
        current_user=current_user,
        submitter=lambda task_id, data: process_stt_task.delay(task_id=task_id, payload=data),
    )


@router.post("/tts", response_model=AITaskResponse)
async def create_tts_task(
    request: TTSRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AITask:
    """
    Create a text-to-speech task that runs locally.
    """
    _require_tier(current_user, required_tier="pro", task_type="tts")
    
    payload = request.dict()
    return await _create_and_dispatch_task(
        task_type=TaskType.TTS,
        payload=payload,
        session=session,
        current_user=current_user,
        submitter=lambda task_id, data: process_tts_task.delay(task_id=task_id, payload=data),
    )


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
    # Validate input constraints before tier check
    if not (1 <= request.n <= 10):
        raise ValidationException("Number of images (n) must be between 1 and 10")
    
    _require_tier(current_user, required_tier="pro", task_type="image")
    
    payload = request.dict()
    return await _create_and_dispatch_task(
        task_type=TaskType.IMAGE,
        payload=payload,
        session=session,
        current_user=current_user,
        submitter=lambda task_id, data: process_image_task.delay(task_id=task_id, payload=data),
    )


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
    if not request.video_url or len(request.video_url) > 2000:
        raise ValidationException("video_url must be provided and less than 2000 characters")
    
    _require_tier(current_user, required_tier="enterprise", task_type="video")
    
    payload = request.dict()
    return await _create_and_dispatch_task(
        task_type=TaskType.VIDEO,
        payload=payload,
        session=session,
        current_user=current_user,
        submitter=lambda task_id, data: process_video_task.delay(task_id=task_id, payload=data),
    )


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
        raise ResourceNotFoundException("Task")
    
    if task.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to access task {task_id} owned by user {task.user_id}",
            extra={
                "event": "unauthorized_task_access",
                "accessing_user_id": current_user.id,
                "task_id": task_id,
                "task_owner_id": task.user_id
            }
        )
        # Return same error as not found to prevent enumeration attacks
        raise ResourceNotFoundException("Task")
    
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
