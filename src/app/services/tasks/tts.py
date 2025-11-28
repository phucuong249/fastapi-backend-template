"""
Local text-to-speech task implementation.
"""

from __future__ import annotations

import base64
import io
import math
import struct
import wave
from typing import Dict, Tuple

from src.app.common.enums import TaskType
from src.app.services.tasks.base import BaseTaskProcessor, TaskResult, TaskValidationError
from src.app.services.tasks.registry import TaskRegistry


class LocalTTSTaskProcessor(BaseTaskProcessor):
    """Deterministic placeholder TTS module."""

    task_type = TaskType.TTS
    name = "local-tts"
    sample_rate = 16000

    def validate_payload(self, payload: Dict[str, str]) -> None:
        text = payload.get("text", "").strip()
        if not text:
            raise TaskValidationError("text is required for TTS tasks")
        payload["text"] = text

    def run(self, payload: Dict[str, str]) -> TaskResult:
        self.validate_payload(payload)

        text = payload["text"]
        voice = payload.get("voice", "alloy")
        speed = float(payload.get("speed", 1.0))

        audio_base64, duration = self._synthesize_wave(text, voice, speed)

        metadata = {
            "voice": voice,
            "duration_seconds": round(duration, 2),
            "sample_rate": self.sample_rate,
            "engine": "local-tts-boilerplate",
        }

        data = {
            "audio_base64": audio_base64,
            "format": "wav",
            "voice": voice,
        }

        return TaskResult(data=data, metadata=metadata)

    def _synthesize_wave(self, text: str, voice: str, speed: float) -> Tuple[str, float]:
        """
        Generate a simple sine wave and return its base64 representation.
        """
        base_freq = 180 + (sum(ord(ch) for ch in voice) % 240)
        duration = max(1.0, min(5.0, len(text) / (15.0 * max(speed, 0.25))))
        total_samples = int(self.sample_rate * duration)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)

            for idx in range(total_samples):
                angle = 2 * math.pi * base_freq * (idx / self.sample_rate)
                amplitude = math.sin(angle)
                sample = int(32767 * 0.2 * amplitude)
                wav_file.writeframes(struct.pack("<h", sample))

        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return encoded, duration


TaskRegistry.register(LocalTTSTaskProcessor())


