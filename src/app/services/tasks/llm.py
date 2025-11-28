"""
Local LLM task implementation.

"""

from __future__ import annotations

import hashlib
import random
import textwrap
from typing import Dict

from src.app.common.enums import TaskType
from src.app.services.tasks.base import BaseTaskProcessor, TaskResult, TaskValidationError
from src.app.services.tasks.registry import TaskRegistry


class LocalLLMTaskProcessor(BaseTaskProcessor):
    """Simple local text generation placeholder."""

    task_type = TaskType.LLM
    name = "local-llm"

    def validate_payload(self, payload: Dict[str, str]) -> None:
        if not payload.get("prompt"):
            raise TaskValidationError("prompt is required for LLM tasks")

    def run(self, payload: Dict[str, str]) -> TaskResult:
        self.validate_payload(payload)

        prompt = payload["prompt"].strip()
        max_tokens = max(1, int(payload.get("max_tokens", 200)))
        temperature = float(payload.get("temperature", 0.7))
        model_name = payload.get("model", "local-mini")

        generated_text = self._generate_text(prompt, max_tokens, temperature)

        metadata = {
            "model": model_name,
            "temperature": temperature,
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(generated_text.split()),
        }

        return TaskResult(
            data={"text": generated_text, "model": model_name},
            metadata=metadata,
        )

    def _generate_text(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """
        Deterministic pseudo generation that keeps everything local.
        """
        words = prompt.replace("\n", " ").split()
        if not words:
            words = ["...", "thoughtful", "response"]

        seed = int(hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # Temperature modulates occasional shuffle
        variability = min(max(temperature, 0.0), 2.0)
        augmented: list[str] = []

        while len(augmented) < max_tokens:
            idx = len(augmented) % len(words)
            choice = words[idx]
            if rng.random() < variability / 4:
                choice = choice.upper()
            if rng.random() < variability / 6:
                augmented.append(rng.choice(["therefore", "notably", "importantly"]))
            augmented.append(choice)

        composed = " ".join(augmented[:max_tokens])
        return textwrap.shorten(composed, width=max_tokens * 8, placeholder=" ...")


# Register processor
TaskRegistry.register(LocalLLMTaskProcessor())


