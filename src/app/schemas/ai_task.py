"""
Pydantic schemas for AI task endpoints.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AITaskBase(BaseModel):
    """Base AI task schema."""
    
    task_type: str = Field(..., description="Task type: llm, stt, tts, image, video")
    input_data: Dict[str, Any] = Field(..., description="Input parameters for the task")


class AITaskCreate(AITaskBase):
    """AI task creation schema."""
    
    pass


class AITaskResponse(AITaskBase):
    """AI task response schema."""
    
    id: int
    user_id: int
    celery_task_id: str
    status: str
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AITaskStatusResponse(BaseModel):
    """AI task status response schema."""
    
    id: int
    task_type: str
    status: str
    progress: float = Field(0.0, ge=0.0, le=100.0)
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class LLMRequest(BaseModel):
    """LLM text generation request."""
    
    prompt: str = Field(..., min_length=1, max_length=10000)
    model: str = Field(default="gpt-3.5-turbo")
    max_tokens: int = Field(default=500, ge=1, le=4000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = Field(default=False)


class STTRequest(BaseModel):
    """Speech-to-text request."""
    
    file_url: str = Field(..., description="URL to audio file")
    language: Optional[str] = Field(None, max_length=10)


class TTSRequest(BaseModel):
    """Text-to-speech request."""
    
    text: str = Field(..., min_length=1, max_length=5000)
    voice: str = Field(default="alloy")
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


class ImageGenerationRequest(BaseModel):
    """Image generation request."""
    
    prompt: str = Field(..., min_length=1, max_length=1000)
    size: str = Field(default="1024x1024", pattern="^\\d+x\\d+$")
    n: int = Field(default=1, ge=1, le=10)


class VideoDetectionRequest(BaseModel):
    """Video detection request."""
    
    video_url: str = Field(..., description="URL to video file")
    detection_type: str = Field(
        default="object",
        description="Detection type: object, pose, face, etc.",
    )
