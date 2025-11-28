"""
Celery application configuration for async task processing.
"""

import logging
from typing import Any, Dict

from celery import Celery, Task

from src.app.common.enums import TaskType
from src.app.core.config import settings
from src.app.services.task_runner import run_task_sync

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
def process_llm_task(self, task_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an LLM task using the local processor registry.
    """
    logger.info("Processing LLM task %s", task_id)
    return run_task_sync(TaskType.LLM, task_id, payload)


@celery_app.task(bind=True, name="ai_backend.tasks.process_stt")
def process_stt_task(self, task_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a speech-to-text task locally.
    """
    logger.info("Processing STT task %s", task_id)
    return run_task_sync(TaskType.STT, task_id, payload)


@celery_app.task(bind=True, name="ai_backend.tasks.process_tts")
def process_tts_task(self, task_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a text-to-speech task locally.
    """
    logger.info("Processing TTS task %s", task_id)
    return run_task_sync(TaskType.TTS, task_id, payload)


@celery_app.task(bind=True, name="ai_backend.tasks.process_image")
def process_image_task(self, task_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an image generation task locally.
    """
    logger.info("Processing image task %s", task_id)
    return run_task_sync(TaskType.IMAGE, task_id, payload)


@celery_app.task(bind=True, name="ai_backend.tasks.process_video")
def process_video_task(self, task_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a video detection task locally.
    """
    logger.info("Processing video task %s", task_id)
    return run_task_sync(TaskType.VIDEO, task_id, payload)
