"""
Celery application configuration for async task processing.
"""

import logging
from typing import Any, Dict

from celery import Celery, Task

from src.app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "ai_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


class CallbackTask(Task):
    """Task base class with callbacks."""
    
    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Success callback."""
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Failure callback."""
        logger.error(f"Task {task_id} failed: {str(exc)}")


celery_app.Task = CallbackTask


# Task definitions
@celery_app.task(bind=True, name="ai_backend.tasks.process_llm")
def process_llm_task(
    self,
    task_id: int,
    prompt: str,
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 500,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """
    Process LLM text generation task.
    
    Args:
        task_id: Database task ID
        prompt: Input prompt
        model: Model name
        max_tokens: Maximum tokens
        temperature: Sampling temperature
        
    Returns:
        Task result
    """
    try:
        import asyncio
        
        from src.app.services.llm import get_llm_service
        
        logger.info(f"Processing LLM task {task_id}")
        
        service = get_llm_service("openai")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            service.generate_text(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        )
        
        return result
    except Exception as e:
        logger.error(f"LLM task {task_id} failed: {str(e)}")
        raise


@celery_app.task(bind=True, name="ai_backend.tasks.process_image")
def process_image_task(
    self,
    task_id: int,
    prompt: str,
    size: str = "1024x1024",
    n: int = 1,
) -> Dict[str, Any]:
    """
    Process image generation task.
    
    Args:
        task_id: Database task ID
        prompt: Image description
        size: Image size
        n: Number of images
        
    Returns:
        Task result
    """
    try:
        logger.info(f"Processing image generation task {task_id}")
        
        # Placeholder for image generation logic
        return {
            "status": "success",
            "images": [],
            "task_id": task_id,
        }
    except Exception as e:
        logger.error(f"Image task {task_id} failed: {str(e)}")
        raise


@celery_app.task(bind=True, name="ai_backend.tasks.process_video")
def process_video_task(
    self,
    task_id: int,
    video_url: str,
    detection_type: str = "object",
) -> Dict[str, Any]:
    """
    Process video detection task.
    
    Args:
        task_id: Database task ID
        video_url: URL to video file
        detection_type: Type of detection
        
    Returns:
        Task result
    """
    try:
        logger.info(f"Processing video detection task {task_id}")
        
        # Placeholder for video detection logic
        return {
            "status": "success",
            "detections": [],
            "task_id": task_id,
        }
    except Exception as e:
        logger.error(f"Video task {task_id} failed: {str(e)}")
        raise
