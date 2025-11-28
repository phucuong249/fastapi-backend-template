"""
Registry for task processors.
"""

from __future__ import annotations

import logging
from typing import Dict

from src.app.common.enums import TaskType
from src.app.services.tasks.base import BaseTaskProcessor, TaskProcessingError

logger = logging.getLogger(__name__)


class TaskRegistry:
    """Global registry of task processors."""

    _processors: Dict[TaskType, BaseTaskProcessor] = {}

    @classmethod
    def register(cls, processor: BaseTaskProcessor) -> None:
        """
        Register a processor instance.
        """
        existing = cls._processors.get(processor.task_type)
        cls._processors[processor.task_type] = processor
        if existing:
            logger.warning(
                "Overriding processor for task %s (%s -> %s)",
                processor.task_type.value,
                existing.name,
                processor.name,
            )
        else:
            logger.info(
                "Registered processor %s for task type %s",
                processor.name,
                processor.task_type.value,
            )

    @classmethod
    def get(cls, task_type: TaskType) -> BaseTaskProcessor:
        """
        Retrieve a processor for the given task type.
        """
        processor = cls._processors.get(task_type)
        if not processor:
            raise TaskProcessingError(f"No processor registered for task type: {task_type.value}")
        return processor

    @classmethod
    def all(cls) -> Dict[TaskType, BaseTaskProcessor]:
        """Expose a copy of the registry (useful for debugging)."""
        return dict(cls._processors)


