from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, model_validator
import logging
import os

# Set up logger for model config
logger = logging.getLogger(__name__)


class BaseModelConfig(BaseModel):
    """Base configuration class for all models."""
    
    model_name: str = Field(..., min_length=1, description="Name of the model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")
    
    # Retry and timeout settings
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    timeout: float = Field(default=30.0, gt=0, description="Request timeout in seconds")
    
    @validator('model_name')
    def validate_model_name(cls, v):
        """Validate model name is not empty."""
        if not v or not v.strip():
            raise ValueError("Model name cannot be empty")
        return v.strip()
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @validator('additional_params')
    def validate_additional_params(cls, v):
        """Validate additional parameters."""
        if not isinstance(v, dict):
            raise ValueError("Additional parameters must be a dictionary")
        return v
    
    def get_api_params(self) -> Dict[str, Any]:
        """Get parameters formatted for API calls."""
        params = {
            'temperature': self.temperature,
            **self.additional_params
        }
        return {k: v for k, v in params.items() if v is not None}
    
    def update_params(self, **kwargs) -> None:
        """Update configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Updated {key} = {value}")
            else:
                self.additional_params[key] = value
                logger.debug(f"Added additional param {key} = {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.dict()
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"  # Prevent additional fields


class OllamaConfig(BaseModelConfig):
    """Enhanced configuration for Ollama model."""
    
    model_name: str = Field(default="llama2", description="Name of the Ollama model to use")
    base_url: str = Field(default="http://localhost:11434", description="Base URL for Ollama API")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Sampling temperature (0.0 to 1.0)")
    
    # Ollama-specific parameters
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    top_k: int = Field(default=40, ge=1, description="Top-k sampling parameter")
    num_ctx: int = Field(default=2048, ge=1, description="Context window size")
    num_thread: int = Field(default=4, ge=1, description="Number of threads to use")
    repeat_penalty: float = Field(default=1.1, ge=0.0, description="Penalty for repeated tokens")
    
    # Generation settings
    stop: Optional[List[str]] = Field(default=None, description="Stop sequences")
    stream: bool = Field(default=True, description="Whether to stream the response")
    
    # Advanced settings
    num_predict: Optional[int] = Field(default=None, ge=1, description="Maximum tokens to generate")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducible generation")
    
    @validator('base_url')
    def validate_base_url(cls, v):
        """Validate base URL format."""
        if not v or not v.strip():
            raise ValueError("Base URL cannot be empty")
        
        v = v.strip().rstrip('/')
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")
        
        return v
    
    @validator('temperature')
    def validate_ollama_temperature(cls, v):
        """Validate temperature for Ollama (0.0 to 1.0)."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Ollama temperature must be between 0.0 and 1.0")
        return v
    
    @validator('stop')
    def validate_stop_sequences(cls, v):
        """Validate stop sequences."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Stop sequences must be a list")
            if not all(isinstance(seq, str) for seq in v):
                raise ValueError("All stop sequences must be strings")
        return v
    
    @validator('num_ctx')
    def validate_context_size(cls, v):
        """Validate context window size."""
        if v > 32768:  # Reasonable upper limit
            logger.warning(f"Large context size ({v}) may cause performance issues")
        return v
    
    def get_api_params(self) -> Dict[str, Any]:
        """Get parameters formatted for Ollama API calls."""
        params = {
            'temperature': self.temperature,
            'top_p': self.top_p,
            'top_k': self.top_k,
            'num_ctx': self.num_ctx,
            'num_thread': self.num_thread,
            'repeat_penalty': self.repeat_penalty,
            'stream': self.stream,
            **self.additional_params
        }
        
        # Add optional parameters if set
        if self.stop is not None:
            params['stop'] = self.stop
        if self.num_predict is not None:
            params['num_predict'] = self.num_predict
        if self.seed is not None:
            params['seed'] = self.seed
        
        return {k: v for k, v in params.items() if v is not None}
    
    def get_health_check_params(self) -> Dict[str, Any]:
        """Get minimal parameters for health checks."""
        return {
            'temperature': 0.1,
            'num_predict': 5,
            'stream': False
        }


class OpenAIConfig(BaseModelConfig):
    """Enhanced configuration for OpenAI model."""
    
    model_name: str = Field(default="gpt-3.5-turbo", description="Name of the OpenAI model to use")
    api_key: Optional[str] = Field(default=None, description="OpenAI API key (if not set in environment)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature (0.0 to 2.0)")
    
    # OpenAI-specific parameters
    max_tokens: Optional[int] = Field(default=None, ge=1, description="Maximum number of tokens to generate")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Top-p sampling parameter")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty (-2.0 to 2.0)")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty (-2.0 to 2.0)")
    
    # Generation settings
    stop: Optional[List[str]] = Field(default=None, description="Stop sequences")
    n: int = Field(default=1, ge=1, le=10, description="Number of completions to generate")
    
    # Advanced settings
    seed: Optional[int] = Field(default=None, description="Random seed for reproducible generation")
    logit_bias: Optional[Dict[str, float]] = Field(default=None, description="Token logit biases")
    user: Optional[str] = Field(default=None, description="User ID for tracking")
    
    @validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key or get from environment."""
        if v is None:
            # Try to get from environment
            env_key = os.getenv('OPENAI_API_KEY')
            if env_key:
                logger.info("Using OpenAI API key from environment")
                return env_key
            else:
                logger.warning("No OpenAI API key provided and OPENAI_API_KEY not set in environment")
                return None
        
        if not v.strip():
            raise ValueError("API key cannot be empty")
        
        if not v.startswith('sk-'):
            logger.warning("API key doesn't start with 'sk-', this might be incorrect")
        
        return v.strip()
    
    @validator('model_name')
    def validate_openai_model(cls, v):
        """Validate OpenAI model name."""
        v = v.strip()
        
        # List of known OpenAI models (not exhaustive, but common ones)
        known_models = {
            'gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-0613',
            'gpt-4', 'gpt-4-0613', 'gpt-4-32k', 'gpt-4-32k-0613',
            'gpt-4-turbo-preview', 'gpt-4-vision-preview',
            'text-davinci-003', 'text-davinci-002'
        }
        
        if v not in known_models:
            logger.warning(f"Model '{v}' is not in the list of known OpenAI models")
        
        return v
    
    @validator('stop')
    def validate_stop_sequences(cls, v):
        """Validate stop sequences."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Stop sequences must be a list")
            if len(v) > 4:
                raise ValueError("OpenAI allows maximum 4 stop sequences")
            if not all(isinstance(seq, str) for seq in v):
                raise ValueError("All stop sequences must be strings")
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        """Validate max tokens."""
        if v is not None and v > 4096:
            logger.warning(f"Large max_tokens ({v}) may exceed model limits")
        return v
    
    @model_validator(mode='after')
    def validate_penalties(self):
        """Validate that penalties are reasonable."""
        freq_penalty = self.frequency_penalty
        pres_penalty = self.presence_penalty
        
        if abs(freq_penalty) > 1.0:
            logger.warning(f"High frequency penalty ({freq_penalty}) may affect generation quality")
        if abs(pres_penalty) > 1.0:
            logger.warning(f"High presence penalty ({pres_penalty}) may affect generation quality")
        
        return self
    
    def get_api_params(self) -> Dict[str, Any]:
        """Get parameters formatted for OpenAI API calls."""
        params = {
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'n': self.n,
            **self.additional_params
        }
        
        # Add optional parameters if set
        if self.max_tokens is not None:
            params['max_tokens'] = self.max_tokens
        if self.stop is not None:
            params['stop'] = self.stop
        if self.seed is not None:
            params['seed'] = self.seed
        if self.logit_bias is not None:
            params['logit_bias'] = self.logit_bias
        if self.user is not None:
            params['user'] = self.user
        
        return {k: v for k, v in params.items() if v is not None}
    
    def get_health_check_params(self) -> Dict[str, Any]:
        """Get minimal parameters for health checks."""
        return {
            'temperature': 0.1,
            'max_tokens': 5,
            'n': 1
        }
    
    def has_valid_api_key(self) -> bool:
        """Check if a valid API key is available."""
        return self.api_key is not None and len(self.api_key.strip()) > 0 