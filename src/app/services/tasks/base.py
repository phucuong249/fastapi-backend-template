"""
Base primitives for local AI task processors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.app.common.enums import TaskType


class TaskValidationError(ValueError):
    """Raised when a processor input payload is invalid."""


class TaskProcessingError(RuntimeError):
    """Raised when a processor cannot complete its execution."""


@dataclass(slots=True)
class TaskResult:
    """
    Normalized payload produced by a task processor.

    Attributes:
        data: Domain specific result payload.
        status: Result status (defaults to "success").
        metadata: Optional dictionary with diagnostics (e.g., model info, timings).
    """

    data: Dict[str, Any]
    status: str = "success"
    metadata: Optional[Dict[str, Any]] = field(default=None)

    def to_payload(self, extra_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert the result to a serializable dictionary.

        Args:
            extra_meta: Optional metadata merged into the payload.

        Returns:
            Dictionary ready for JSON serialization.
        """
        payload: Dict[str, Any] = {"status": self.status, "data": self.data}
        merged_meta: Dict[str, Any] = {}

        if self.metadata:
            merged_meta.update(self.metadata)
        if extra_meta:
            merged_meta.update(extra_meta)

        if merged_meta:
            payload["meta"] = merged_meta

        return payload


class BaseTaskProcessor(ABC):
    """
    Base class for any local AI task processor.

    Concrete implementations must define the `task_type` they handle and implement
    the synchronous `run` method that returns a `TaskResult`.
    """

    task_type: TaskType
    name: str = "base-task"

    def __init__(self) -> None:
        if not getattr(self, "task_type", None):
            raise ValueError("Task processors must set a TaskType via `task_type`.")

    def validate_payload(self, payload: Dict[str, Any]) -> None:
        """
        Optional hook to validate an incoming payload before execution.
        """

    @abstractmethod
    def run(self, payload: Dict[str, Any]) -> TaskResult:
        """
        Execute the task synchronously and return a result.
        """


