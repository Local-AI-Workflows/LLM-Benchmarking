from typing import Dict, Any, Optional
import openai
from pydantic import BaseModel
from .base_model import BaseLLMModel
from .model_config import OpenAIConfig

class ModelResponse(BaseModel):
    """Container for model responses."""
    text: str
    metadata: Dict[str, Any]

class OpenAIModel(BaseLLMModel):
    """Wrapper for OpenAI API interactions."""
    
    def __init__(self, config: OpenAIConfig = None):
        """
        Initialize the OpenAI model wrapper.
        
        Args:
            config: Configuration for the OpenAI model. If None, default config will be used.
        """
        self.config = config or OpenAIConfig()
        self._model_name = self.config.model_name
        if self.config.api_key:
            openai.api_key = self.config.api_key
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate a response for the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters to override config settings
            
        Returns:
            ModelResponse containing the generated text and metadata
        """
        try:
            # Merge config with any overrides from kwargs
            params = self.config.dict(exclude={'model_name', 'api_key', 'additional_params'})
            params.update(self.config.additional_params)
            params.update(kwargs)
            
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                **params
            )
            
            return ModelResponse(
                text=response.choices[0].message.content,
                metadata={
                    "model": self.model_name,
                    "usage": response.usage.dict(),
                    "finish_reason": response.choices[0].finish_reason,
                    "config": self.config.dict()
                }
            )
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")
    
    def __str__(self) -> str:
        return f"OpenAI Model: {self.model_name}" 