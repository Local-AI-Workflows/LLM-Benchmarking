from typing import Dict, Any, Optional
import openai
from pydantic import BaseModel

class ModelResponse(BaseModel):
    """Container for model responses."""
    text: str
    metadata: Dict[str, Any]

class OpenAIModel:
    """Wrapper for OpenAI API interactions."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        """
        Initialize the OpenAI model wrapper.
        
        Args:
            model_name: The OpenAI model to use
            api_key: Optional API key (will use environment variable if not provided)
        """
        self.model_name = model_name
        if api_key:
            openai.api_key = api_key
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate a response for the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional arguments for the OpenAI API
            
        Returns:
            ModelResponse containing the generated text and metadata
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            return ModelResponse(
                text=response.choices[0].message.content,
                metadata={
                    "model": self.model_name,
                    "usage": response.usage.dict(),
                    "finish_reason": response.choices[0].finish_reason
                }
            )
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")
    
    def __str__(self) -> str:
        return f"OpenAI Model: {self.model_name}" 