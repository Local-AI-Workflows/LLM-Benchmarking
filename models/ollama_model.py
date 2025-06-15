from typing import Dict, Any
import aiohttp
import json
from pydantic import BaseModel
from .base_model import BaseLLMModel
from .model_config import OllamaConfig


class ModelResponse(BaseModel):
    """Container for model responses."""
    text: str
    metadata: Dict[str, Any]


class OllamaModel(BaseLLMModel):
    """Wrapper for Ollama API interactions."""

    def __init__(self, config: OllamaConfig = None):
        """
        Initialize the Ollama model wrapper.
        
        Args:
            config: Configuration for the Ollama model. If None, default config will be used.
        """
        self.config = config or OllamaConfig()
        self._model_name = self.config.model_name
        self.base_url = self.config.base_url.rstrip('/')

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate a response for the given prompt using Ollama's streaming API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters to override config settings
            
        Returns:
            ModelResponse containing the generated text and metadata
        """
        try:
            # Merge config with any overrides from kwargs
            params = self.config.dict(exclude={'model_name', 'base_url', 'additional_params'})
            params.update(self.config.additional_params)
            params.update(kwargs)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": self.model_name,
                            "prompt": prompt,
                            **params
                        }
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status}")

                    generated_text = ""
                    final_metadata = {}
                    async for line_bytes in response.content:
                        line = line_bytes.decode("utf-8").strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            generated_text += data.get("response", "")
                            final_metadata = data
                        except json.JSONDecodeError as e:
                            print(f"Skipping invalid JSON line: {line} ({e})")

                    return ModelResponse(
                        text=generated_text,
                        metadata={
                            "model": self.model_name,
                            "total_duration": final_metadata.get("total_duration", 0),
                            "load_duration": final_metadata.get("load_duration", 0),
                            "prompt_eval_duration": final_metadata.get("prompt_eval_duration", 0),
                            "eval_duration": final_metadata.get("eval_duration", 0),
                            "eval_count": final_metadata.get("eval_count", 0),
                            "config": self.config.dict()
                        }
                    )
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")

    def __str__(self) -> str:
        return f"Ollama Model: {self.model_name}"

