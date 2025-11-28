"""
Task processor package.

Importing this package ensures that all processors are registered with the
`TaskRegistry`, which allows Celery workers and the FastAPI app to resolve the
implementations by `TaskType`.
"""

from src.app.services.tasks.registry import TaskRegistry

# Import processors for side effects (registration)
from . import image as _image  # noqa: F401
from . import llm as _llm  # noqa: F401
from . import stt as _stt  # noqa: F401
from . import tts as _tts  # noqa: F401
from . import video as _video  # noqa: F401

__all__ = ["TaskRegistry"]

