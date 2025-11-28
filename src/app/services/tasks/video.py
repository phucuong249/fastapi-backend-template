"""
Local video detection task implementation.
"""

from __future__ import annotations

import hashlib
import random
from typing import Dict, List

from src.app.common.enums import TaskType
from src.app.services.tasks.base import BaseTaskProcessor, TaskResult, TaskValidationError
from src.app.services.tasks.registry import TaskRegistry


class LocalVideoTaskProcessor(BaseTaskProcessor):
    """Deterministic placeholder for video analytics."""

    task_type = TaskType.VIDEO
    name = "local-video"

    def validate_payload(self, payload: Dict[str, str]) -> None:
        video_url = payload.get("video_url", "").strip()
        if not video_url:
            raise TaskValidationError("video_url is required for video tasks")
        if len(video_url) > 2000:
            raise TaskValidationError("video_url is too long")
        payload["video_url"] = video_url

    def run(self, payload: Dict[str, str]) -> TaskResult:
        self.validate_payload(payload)

        video_url = payload["video_url"]
        detection_type = payload.get("detection_type", "object")
        detections = self._build_detections(video_url, detection_type)

        metadata = {
            "engine": "local-video-boilerplate",
            "detection_type": detection_type,
            "video_fingerprint": hashlib.md5(video_url.encode("utf-8")).hexdigest()[:12],
        }

        return TaskResult(
            data={"detections": detections, "detection_type": detection_type, "video_url": video_url},
            metadata=metadata,
        )

    def _build_detections(self, video_url: str, detection_type: str) -> List[Dict[str, float]]:
        seed = int(hashlib.sha1(video_url.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random(seed)
        detections: List[Dict[str, float]] = []

        for idx in range(3):
            detections.append(
                {
                    "label": f"{detection_type}_signal_{idx+1}",
                    "confidence": round(0.5 + rng.random() * 0.49, 2),
                    "timestamp": round(idx * 1.25 + rng.random() * 0.5, 2),
                }
            )

        return detections


TaskRegistry.register(LocalVideoTaskProcessor())


