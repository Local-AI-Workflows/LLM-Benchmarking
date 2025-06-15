from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseLLMModel(ABC):
    """Base class for all LLM model implementations."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> "ModelResponse":
        """
        Generate a response for the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional arguments for the model API
            
        Returns:
            ModelResponse containing the generated text and metadata
        """
        raise NotImplementedError()
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the model."""
        raise NotImplementedError() 