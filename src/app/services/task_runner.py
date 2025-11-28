"""
Utilities for executing AI tasks and persisting their lifecycle.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from time import perf_counter
from typing import Any, Dict

from src.app.common.enums import TaskStatus, TaskType
from src.app.db.models import AITask
from src.app.db.session import async_session_maker
from src.app.services.tasks import TaskRegistry
from src.app.services.tasks.base import TaskProcessingError

logger = logging.getLogger(__name__)


async def execute_task_async(task_type: TaskType, task_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a registered task processor and persist its result.
    """
    processor = TaskRegistry.get(task_type)
    await _update_task(task_id, status=TaskStatus.PROCESSING.value, error_message=None)

    start = perf_counter()

    try:
        result = processor.run(payload)
    except Exception as exc:  # noqa: BLE001 - surface downstream errors
        await _handle_failure(task_id, exc)
        raise

    execution_ms = round((perf_counter() - start) * 1000, 2)
    output_payload = result.to_payload(extra_meta={"execution_ms": execution_ms})

    await _update_task(
        task_id,
        status=TaskStatus.COMPLETED.value,
        output_data=json.dumps(output_payload),
        completed_at=datetime.utcnow(),
    )

    logger.info(
        "Task %s (%s) completed locally in %sms",
        task_id,
        task_type.value,
        execution_ms,
    )

    return output_payload


def run_task_sync(task_type: TaskType, task_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper for Celery tasks (which are synchronous functions).
    """
    return asyncio.run(execute_task_async(task_type, task_id, payload))


async def _handle_failure(task_id: int, exc: Exception) -> None:
    logger.exception("Task %s failed: %s", task_id, exc)
    await _update_task(
        task_id,
        status=TaskStatus.FAILED.value,
        error_message=str(exc),
        completed_at=datetime.utcnow(),
    )


async def _update_task(task_id: int, **fields: Any) -> AITask:
    async with async_session_maker() as session:
        task = await session.get(AITask, task_id)
        if not task:
            raise TaskProcessingError(f"Task with id={task_id} not found")

        for key, value in fields.items():
            setattr(task, key, value)

        task.updated_at = datetime.utcnow()
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


