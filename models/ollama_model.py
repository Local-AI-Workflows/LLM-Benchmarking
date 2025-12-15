from typing import Dict, Any, List
import aiohttp
import json
import logging
import time
import asyncio
from .base_model import BaseLLMModel
from .model_config import OllamaConfig
from .responses import ModelResponse

# Set up logger for Ollama model
logger = logging.getLogger(__name__)


class OllamaModel(BaseLLMModel):
    """
    Enhanced wrapper for Ollama API interactions.
    
    Provides robust error handling, retry logic, and comprehensive logging
    for Ollama model interactions.
    """

    def __init__(self, config: OllamaConfig = None):
        """
        Initialize the Ollama model wrapper.
        
        Args:
            config: Configuration for the Ollama model. If None, default config will be used.
        """
        super().__init__()
        
        self.config = config or OllamaConfig()
        self._model_name = self.config.model_name
        self.base_url = self.config.base_url.rstrip('/')
        
        logger.info(f"Initialized Ollama model: {self._model_name} at {self.base_url}")

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @property
    def is_available(self) -> bool:
        """Check if the Ollama server is available (synchronous check)."""
        # For synchronous property, we return True by default
        # Actual availability check is done in health_check method
        return True

    async def check_server_availability(self) -> bool:
        """Async method to check if the Ollama server is available."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=5) as response:
                    return response.status == 200
        except Exception:
            return False

    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate a response for the given prompt using Ollama's API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters to override config settings
            
        Returns:
            ModelResponse containing the generated text and metadata
            
        Raises:
            Exception: If response generation fails
        """
        start_time = time.time()
        
        try:
            # Merge config with any overrides from kwargs
            api_params = self.config.get_api_params()
            api_params.update(kwargs)
            
            logger.debug(f"Calling Ollama API with model: {self.model_name}")
            logger.debug(f"API parameters: {api_params}")
            
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                **api_params
            }
            
            # Configure timeout - for streaming, we need longer read timeout
            # total: total time for the request
            # sock_read: time to wait between reading chunks (important for streaming)
            timeout_config = aiohttp.ClientTimeout(
                total=self.config.timeout * 10,  # Allow 10x for total (for long generations)
                sock_read=self.config.timeout * 2  # Allow 2x between chunks
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/api/generate",
                        json=request_data,
                        timeout=timeout_config
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_msg = f"Ollama API error (status {response.status}): {error_text}"
                        logger.error(error_msg)
                        raise Exception(error_msg)

                    generated_text = ""
                    final_metadata = {}
                    
                    # Handle streaming response
                    if api_params.get('stream', True):
                        async for line_bytes in response.content:
                            line = line_bytes.decode("utf-8").strip()
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                                generated_text += data.get("response", "")
                                final_metadata = data
                                
                                # Check if generation is complete
                                if data.get("done", False):
                                    break
                                    
                            except json.JSONDecodeError as e:
                                logger.warning(f"Skipping invalid JSON line: {line} ({e})")
                    else:
                        # Handle non-streaming response
                        response_data = await response.json()
                        generated_text = response_data.get("response", "")
                        final_metadata = response_data

                    response_time = time.time() - start_time
                    
                    # Create enhanced response
                    model_response = ModelResponse(
                        text=generated_text,
                        model_name=self.model_name,
                        response_time=response_time,
                        prompt_length=len(prompt),
                        token_count=self._estimate_token_count(generated_text),
                        metadata={
                            "model": self.model_name,
                            "config": self.config.to_dict(),
                            "api_version": "ollama",
                            "base_url": self.base_url,
                            "request_params": api_params
                        }
                    )
                    
                    # Add Ollama-specific metadata
                    ollama_stats = {}
                    for key in ['total_duration', 'load_duration', 'prompt_eval_duration', 
                               'eval_duration', 'eval_count', 'prompt_eval_count']:
                        if key in final_metadata:
                            ollama_stats[key] = final_metadata[key]
                    
                    if ollama_stats:
                        model_response.update_usage_stats(ollama_stats)
                        model_response.add_metadata("ollama_stats", ollama_stats)
                    
                    # Add performance metrics
                    if 'eval_count' in final_metadata and 'eval_duration' in final_metadata:
                        eval_count = final_metadata['eval_count']
                        eval_duration = final_metadata['eval_duration']
                        if eval_duration > 0:
                            tokens_per_second = (eval_count * 1e9) / eval_duration  # Convert nanoseconds
                            model_response.add_metadata("tokens_per_second", tokens_per_second)
                    
                    logger.info(f"Successfully generated response in {response_time:.2f}s "
                               f"({len(generated_text)} chars)")
                    
                    return model_response
                    
        except aiohttp.ClientError as e:
            error_msg = f"Ollama connection error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except (aiohttp.ServerTimeoutError, asyncio.TimeoutError) as e:
            error_msg = f"Ollama request timeout: The request took too long. This might mean the Ollama server is not responding or the model is taking too long to generate. Error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response from Ollama: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error during Ollama generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)

    def _estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token for English text
        return max(1, len(text) // 4)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the Ollama model.
        
        Returns:
            Dictionary with health status
        """
        try:
            # First check if server is available
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=5) as response:
                    if response.status != 200:
                        return {
                            'status': 'unhealthy',
                            'model_name': self.model_name,
                            'error': f'Ollama server not available (status: {response.status})',
                            'timestamp': time.time(),
                            'server_available': False
                        }
            
            # Check if specific model is available
            if not await self._is_model_available():
                return {
                    'status': 'unhealthy',
                    'model_name': self.model_name,
                    'error': f'Model {self.model_name} not found on server',
                    'timestamp': time.time(),
                    'server_available': True,
                    'model_available': False
                }
            
            # Test generation
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
                'server_available': True,
                'model_available': True
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'model_name': self.model_name,
                'error': str(e),
                'timestamp': time.time(),
                'server_available': False
            }

    async def _is_model_available(self) -> bool:
        """Check if the specific model is available on the Ollama server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('models', [])
                        available_models = [model['name'] for model in models]
                        return self.model_name in available_models
        except Exception:
            pass
        return False

    async def get_available_models(self) -> List[str]:
        """
        Get list of available models on the Ollama server.
        
        Returns:
            List of available model names
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('models', [])
                        return [model['name'] for model in models]
        except Exception as e:
            logger.error(f"Failed to get available models: {str(e)}")
        return []

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get detailed information about the model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'model_type': 'ollama',
            'provider': 'Ollama',
            'base_url': self.base_url,
            'config': self.config.to_dict(),
            'supported_features': [
                'text_generation',
                'streaming',
                'temperature_control',
                'context_window',
                'stop_sequences',
                'custom_parameters'
            ],
            'max_context_length': self.config.num_ctx,
            'supports_batch': True,  # Our implementation supports batch processing
            'local_deployment': True,
            'cost_per_token': 0.0  # Local deployment is free
        }

    def __str__(self) -> str:
        """String representation of the model."""
        return f"Ollama Model: {self.model_name}"

    def __repr__(self) -> str:
        """Detailed string representation."""
        stats = self.get_stats()
        return (f"OllamaModel(model_name='{self.model_name}', "
                f"base_url='{self.base_url}', "
                f"requests={stats['total_requests']}, "
                f"success_rate={stats['success_rate']:.2%})")

