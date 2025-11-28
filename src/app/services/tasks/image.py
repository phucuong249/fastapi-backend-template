"""
Local image generation task implementation.
"""

from __future__ import annotations

import base64
import hashlib
import html
from typing import Dict, Tuple

from src.app.common.enums import TaskType
from src.app.services.tasks.base import BaseTaskProcessor, TaskResult, TaskValidationError
from src.app.services.tasks.registry import TaskRegistry


class LocalImageTaskProcessor(BaseTaskProcessor):
    """Generates deterministic SVG placeholders."""

    task_type = TaskType.IMAGE
    name = "local-image"

    def validate_payload(self, payload: Dict[str, str]) -> None:
        prompt = payload.get("prompt", "").strip()
        if not prompt:
            raise TaskValidationError("prompt is required for image tasks")

        size_str = payload.get("size", "512x512")
        try:
            self._parse_size(size_str)
        except ValueError as exc:
            raise TaskValidationError(str(exc)) from exc

        n = int(payload.get("n", 1))
        if not 1 <= n <= 10:
            raise TaskValidationError("n must be between 1 and 10")

        payload["prompt"] = prompt
        payload["size"] = size_str
        payload["n"] = n

    def run(self, payload: Dict[str, str]) -> TaskResult:
        self.validate_payload(payload)

        prompt = payload["prompt"]
        size = payload["size"]
        n = int(payload["n"])
        width, height = self._parse_size(size)

        images = [self._build_svg(prompt, width, height, idx) for idx in range(n)]
        metadata = {
            "engine": "local-image-boilerplate",
            "size": size,
            "count": n,
        }

        return TaskResult(
            data={"images": images, "size": size, "prompt": prompt},
            metadata=metadata,
        )

    def _parse_size(self, size: str) -> Tuple[int, int]:
        if "x" not in size:
            raise ValueError("size must be in the format WIDTHxHEIGHT")
        width_str, height_str = size.lower().split("x", maxsplit=1)
        width = int(width_str)
        height = int(height_str)
        if width <= 0 or height <= 0:
            raise ValueError("size dimensions must be positive")
        return width, height

    def _build_svg(self, prompt: str, width: int, height: int, index: int) -> str:
        seed = hashlib.sha256(f"{prompt}-{index}".encode("utf-8")).hexdigest()
        background = f"#{seed[:6]}"
        accent = f"#{seed[6:12]}"
        escaped_prompt = html.escape(prompt[:80])

        svg = f"""
            <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
                <rect width="100%" height="100%" fill="{background}" rx="24" ry="24"/>
                <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
                      font-family="Arial, sans-serif" font-size="{max(12, width // 24)}"
                      fill="{accent}">
                    {escaped_prompt}
                </text>
            </svg>
        """.strip()

        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"


TaskRegistry.register(LocalImageTaskProcessor())


