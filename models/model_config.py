from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class OllamaConfig(BaseModel):
    """Configuration for Ollama model."""
    model_name: str = Field(default="llama2", description="Name of the Ollama model to use")
    base_url: str = Field(default="http://localhost:11434", description="Base URL for Ollama API")
    temperature: float = Field(default=0.7, description="Sampling temperature (0.0 to 1.0)")
    top_p: float = Field(default=0.9, description="Top-p sampling parameter")
    top_k: int = Field(default=40, description="Top-k sampling parameter")
    num_ctx: int = Field(default=2048, description="Context window size")
    num_thread: int = Field(default=4, description="Number of threads to use")
    repeat_penalty: float = Field(default=1.1, description="Penalty for repeated tokens")
    stop: Optional[list[str]] = Field(default=None, description="Stop sequences")
    stream: bool = Field(default=True, description="Whether to stream the response")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters to pass to Ollama API")


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI model."""
    model_name: str = Field(default="gpt-3.5-turbo", description="Name of the OpenAI model to use")
    api_key: Optional[str] = Field(default=None, description="OpenAI API key (if not set in environment)")
    temperature: float = Field(default=0.7, description="Sampling temperature (0.0 to 2.0)")
    max_tokens: Optional[int] = Field(default=None, description="Maximum number of tokens to generate")
    top_p: float = Field(default=1.0, description="Top-p sampling parameter")
    frequency_penalty: float = Field(default=0.0, description="Frequency penalty (-2.0 to 2.0)")
    presence_penalty: float = Field(default=0.0, description="Presence penalty (-2.0 to 2.0)")
    stop: Optional[list[str]] = Field(default=None, description="Stop sequences")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters to pass to OpenAI API") 