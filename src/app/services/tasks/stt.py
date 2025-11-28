"""
Local speech-to-text task implementation.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict

from src.app.common.enums import TaskType
from src.app.services.tasks.base import BaseTaskProcessor, TaskResult, TaskValidationError
from src.app.services.tasks.registry import TaskRegistry


class LocalSTTTaskProcessor(BaseTaskProcessor):
    """Deterministic placeholder STT module."""

    task_type = TaskType.STT
    name = "local-stt"

    def validate_payload(self, payload: Dict[str, str]) -> None:
        file_url = payload.get("file_url", "").strip()
        if not file_url:
            raise TaskValidationError("file_url is required for STT tasks")
        if len(file_url) > 2000:
            raise TaskValidationError("file_url is too long")
        payload["file_url"] = file_url

    def run(self, payload: Dict[str, str]) -> TaskResult:
        self.validate_payload(payload)

        file_url = payload["file_url"]
        language = payload.get("language") or "auto"
        transcript = self._build_transcript(file_url)

        data = {
            "transcript": transcript,
            "language": language,
            "segments": [
                {
                    "text": transcript,
                    "start": 0.0,
                    "end": max(1.5, len(transcript.split()) * 0.35),
                }
            ],
        }

        metadata = {
            "audio_fingerprint": hashlib.sha1(file_url.encode("utf-8")).hexdigest()[:12],
            "engine": "local-stt-boilerplate",
        }

        return TaskResult(data=data, metadata=metadata)

    def _build_transcript(self, file_url: str) -> str:
        parsed = urlparse(file_url)
        name = Path(parsed.path or "audio").stem or "audio"
        words = [chunk.capitalize() for chunk in name.replace("_", " ").split()]
        if not words:
            words = ["Local", "Transcript"]
        return " ".join(words)


TaskRegistry.register(LocalSTTTaskProcessor())


