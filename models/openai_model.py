from typing import Dict, Any, Optional
import openai
import logging
import time
from .base_model import BaseLLMModel
from .model_config import OpenAIConfig
from .responses import ModelResponse

# Set up logger for OpenAI model
logger = logging.getLogger(__name__)


class OpenAIModel(BaseLLMModel):
    """
    Enhanced wrapper for OpenAI API interactions.
    
    Provides robust error handling, retry logic, and comprehensive logging
    for OpenAI model interactions.
    """
    
    def __init__(self, config: OpenAIConfig = None):
        """
        Initialize the OpenAI model wrapper.
        
        Args:
            config: Configuration for the OpenAI model. If None, default config will be used.
        """
        super().__init__()
        
        self.config = config or OpenAIConfig()
        self._model_name = self.config.model_name
        
        # Set API key if provided
        if self.config.api_key:
            openai.api_key = self.config.api_key
            logger.info("OpenAI API key configured")
        else:
            logger.warning("No OpenAI API key configured - requests may fail")
        
        logger.info(f"Initialized OpenAI model: {self._model_name}")
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name
    
    @property
    def is_available(self) -> bool:
        """Check if the model is available (has valid API key)."""
        return self.config.has_valid_api_key()
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate a response for the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters to override config settings
            
        Returns:
            ModelResponse containing the generated text and metadata
            
        Raises:
            Exception: If response generation fails
        """
        if not self.is_available:
            raise Exception("OpenAI API key not available")
        
        start_time = time.time()
        
        try:
            # Merge config with any overrides from kwargs
            api_params = self.config.get_api_params()
            api_params.update(kwargs)
            
            logger.debug(f"Calling OpenAI API with model: {self.model_name}")
            logger.debug(f"API parameters: {self._sanitize_params_for_logging(api_params)}")
            
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                **api_params
            )
            
            response_time = time.time() - start_time
            generated_text = response.choices[0].message.content
            
            # Create enhanced response
            model_response = ModelResponse(
                text=generated_text,
                model_name=self.model_name,
                response_time=response_time,
                prompt_length=len(prompt),
                finish_reason=response.choices[0].finish_reason,
                token_count=response.usage.total_tokens if hasattr(response, 'usage') else None,
                metadata={
                    "model": self.model_name,
                    "finish_reason": response.choices[0].finish_reason,
                    "config": self.config.to_dict(),
                    "api_version": "openai",
                    "request_params": self._sanitize_params_for_logging(api_params)
                }
            )
            
            # Add usage statistics
            if hasattr(response, 'usage'):
                usage_stats = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                model_response.update_usage_stats(usage_stats)
                model_response.add_metadata("usage", usage_stats)
            
            # Add response metadata
            model_response.add_metadata("response_id", response.id if hasattr(response, 'id') else None)
            model_response.add_metadata("created", response.created if hasattr(response, 'created') else None)
            
            logger.info(f"Successfully generated response in {response_time:.2f}s "
                       f"({model_response.token_count} tokens)")
            
            return model_response
            
        except openai.error.RateLimitError as e:
            error_msg = f"OpenAI rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except openai.error.InvalidRequestError as e:
            error_msg = f"Invalid OpenAI request: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except openai.error.AuthenticationError as e:
            error_msg = f"OpenAI authentication failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except openai.error.APIConnectionError as e:
            error_msg = f"OpenAI API connection failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except openai.error.APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error during OpenAI generation: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _sanitize_params_for_logging(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize parameters for safe logging (remove sensitive data).
        
        Args:
            params: Parameters to sanitize
            
        Returns:
            Sanitized parameters
        """
        sanitized = params.copy()
        
        # Remove or mask sensitive parameters
        sensitive_keys = ['api_key', 'authorization', 'token']
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "[REDACTED]"
        
        return sanitized
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the OpenAI model.
        
        Returns:
            Dictionary with health status
        """
        try:
            if not self.is_available:
                return {
                    'status': 'unhealthy',
                    'model_name': self.model_name,
                    'error': 'No valid API key available',
                    'timestamp': time.time()
                }
            
            # Use minimal parameters for health check
            health_params = self.config.get_health_check_params()
            
            start_time = time.time()
            response = await self.generate("Hello", **health_params)
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy' if response.is_successful else 'unhealthy',
                'model_name': self.model_name,
                'response_time': response_time,
                'test_successful': response.is_successful,
                'timestamp': time.time(),
                'api_available': True
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'model_name': self.model_name,
                'error': str(e),
                'timestamp': time.time(),
                'api_available': False
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get detailed information about the model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'model_type': 'openai',
            'provider': 'OpenAI',
            'config': self.config.to_dict(),
            'api_key_available': self.is_available,
            'supported_features': [
                'chat_completion',
                'streaming',
                'function_calling',
                'system_messages',
                'temperature_control',
                'token_limits',
                'stop_sequences'
            ],
            'max_context_length': self._get_max_context_length(),
            'supports_batch': False,  # OpenAI doesn't support batch processing in this implementation
            'cost_per_token': self._get_cost_info()
        }
    
    def _get_max_context_length(self) -> int:
        """Get maximum context length for the model."""
        context_lengths = {
            'gpt-3.5-turbo': 4096,
            'gpt-3.5-turbo-16k': 16384,
            'gpt-4': 8192,
            'gpt-4-32k': 32768,
            'gpt-4-turbo-preview': 128000,
        }
        return context_lengths.get(self.model_name, 4096)
    
    def _get_cost_info(self) -> Dict[str, float]:
        """Get cost information for the model (approximate)."""
        # Approximate costs in USD per 1K tokens (as of 2024)
        costs = {
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
        }
        return costs.get(self.model_name, {'input': 0.001, 'output': 0.002})
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"OpenAI Model: {self.model_name}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        stats = self.get_stats()
        return (f"OpenAIModel(model_name='{self.model_name}', "
                f"api_key_available={self.is_available}, "
                f"requests={stats['total_requests']}, "
                f"success_rate={stats['success_rate']:.2%})") 