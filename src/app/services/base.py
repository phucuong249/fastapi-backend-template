"""
Base service classes using Strategy Pattern for AI modules.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseLLMService(ABC):
    """Abstract base class for LLM services."""
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 500,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate text using LLM.
        
        Args:
            prompt: Input prompt
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            
        Returns:
            Generated text and metadata
        """
        pass


class BaseSTTService(ABC):
    """Abstract base class for Speech-to-Text services."""
    
    @abstractmethod
    async def transcribe(
        self,
        file_url: str,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.
        
        Args:
            file_url: URL to audio file
            language: Language code (optional)
            
        Returns:
            Transcription and metadata
        """
        pass


class BaseTTSService(ABC):
    """Abstract base class for Text-to-Speech services."""
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text.
        
        Args:
            text: Input text
            voice: Voice identifier
            speed: Speech speed (0.25 to 4.0)
            
        Returns:
            Audio URL and metadata
        """
        pass


class BaseImageService(ABC):
    """Abstract base class for Image Generation services."""
    
    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        n: int = 1,
    ) -> Dict[str, Any]:
        """
        Generate images from text prompt.
        
        Args:
            prompt: Text description
            size: Image size (e.g., "1024x1024")
            n: Number of images to generate
            
        Returns:
            Image URLs and metadata
        """
        pass


class BaseVideoService(ABC):
    """Abstract base class for Video Processing services."""
    
    @abstractmethod
    async def detect_objects(
        self,
        video_url: str,
        detection_type: str = "object",
    ) -> Dict[str, Any]:
        """
        Detect objects/poses/faces in video.
        
        Args:
            video_url: URL to video file
            detection_type: Type of detection (object, pose, face, etc.)
            
        Returns:
            Detection results and metadata
        """
        pass
