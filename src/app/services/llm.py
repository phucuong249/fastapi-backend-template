"""
LLM service implementations for different providers.
"""

import logging
from typing import Any, Dict, Optional

import httpx
from openai import AsyncOpenAI

from src.app.core.config import settings
from src.app.services.base import BaseLLMService

logger = logging.getLogger(__name__)


class OpenAIService(BaseLLMService):
    """OpenAI LLM service implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI service.
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def generate_text(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 500,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate text using OpenAI API.
        
        Args:
            prompt: Input prompt
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            
        Returns:
            Generated text and metadata
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream,
            )
            
            if stream:
                return {
                    "status": "streaming",
                    "stream": response,
                    "model": model,
                }
            
            return {
                "status": "success",
                "text": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
            }


class LocalLlamaService(BaseLLMService):
    """Local Llama LLM service implementation."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        Initialize Local Llama service.
        
        Args:
            base_url: Base URL for local Llama server
        """
        self.base_url = base_url
    
    async def generate_text(
        self,
        prompt: str,
        model: str = "llama2",
        max_tokens: int = 500,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate text using local Llama model.
        
        Args:
            prompt: Input prompt
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            
        Returns:
            Generated text and metadata
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/completions",
                    json={
                        "prompt": prompt,
                        "model": model,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": stream,
                    },
                    timeout=300.0,
                )
                response.raise_for_status()
                
                data = response.json()
                return {
                    "status": "success",
                    "text": data["choices"][0]["text"],
                    "model": model,
                    "usage": data.get("usage", {}),
                }
        except Exception as e:
            logger.error(f"Local Llama API error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
            }


class HuggingFaceService(BaseLLMService):
    """HuggingFace LLM service implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize HuggingFace service.
        
        Args:
            api_key: HuggingFace API key
        """
        self.api_key = api_key
    
    async def generate_text(
        self,
        prompt: str,
        model: str = "gpt2",
        max_tokens: int = 500,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate text using HuggingFace API.
        
        Args:
            prompt: Input prompt
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            
        Returns:
            Generated text and metadata
        """
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers=headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": max_tokens,
                            "temperature": temperature,
                        },
                    },
                    timeout=300.0,
                )
                response.raise_for_status()
                
                data = response.json()
                return {
                    "status": "success",
                    "text": data[0]["generated_text"],
                    "model": model,
                }
        except Exception as e:
            logger.error(f"HuggingFace API error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
            }


# Service factory
def get_llm_service(provider: str = "openai") -> BaseLLMService:
    """
    Get LLM service instance based on provider.
    
    Args:
        provider: Provider name (openai, llama, huggingface)
        
    Returns:
        LLM service instance
    """
    if provider == "openai":
        return OpenAIService()
    elif provider == "llama":
        return LocalLlamaService()
    elif provider == "huggingface":
        return HuggingFaceService()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
