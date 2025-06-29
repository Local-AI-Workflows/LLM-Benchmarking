from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import time
from datetime import datetime

# Set up logger for base model
logger = logging.getLogger(__name__)


class BaseLLMModel(ABC):
    """
    Enhanced base class for all LLM model implementations.
    
    Provides common functionality for model management, error handling,
    and performance tracking.
    """
    
    def __init__(self):
        """Initialize base model with tracking capabilities."""
        self._request_count = 0
        self._error_count = 0
        self._total_response_time = 0.0
        self._last_request_time: Optional[datetime] = None
        logger.info(f"Initialized model: {self.__class__.__name__}")
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> "ModelResponse":
        """
        Generate a response for the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional arguments for the model API
            
        Returns:
            ModelResponse containing the generated text and metadata
            
        Raises:
            Exception: If response generation fails
        """
        raise NotImplementedError()
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the model."""
        raise NotImplementedError()
    
    @property
    def model_type(self) -> str:
        """Get the type/provider of the model (e.g., 'openai', 'ollama')."""
        return self.__class__.__name__.lower().replace('model', '')
    
    @property
    def is_available(self) -> bool:
        """Check if the model is available for use."""
        return True  # Default implementation, can be overridden
    
    async def generate_with_retry(
        self, 
        prompt: str, 
        max_retries: int = 3, 
        retry_delay: float = 1.0,
        **kwargs
    ) -> "ModelResponse":
        """
        Generate response with automatic retry on failure.
        
        Args:
            prompt: The input prompt
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            **kwargs: Additional arguments for generate()
            
        Returns:
            ModelResponse
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Generate attempt {attempt + 1}/{max_retries + 1} for {self.model_name}")
                return await self._generate_with_tracking(prompt, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Generate attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    import asyncio
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed for {self.model_name}")
        
        # If we get here, all attempts failed
        self._error_count += 1
        raise Exception(f"Failed to generate response after {max_retries + 1} attempts: {str(last_error)}")
    
    async def _generate_with_tracking(self, prompt: str, **kwargs) -> "ModelResponse":
        """
        Internal method to generate response with performance tracking.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional arguments
            
        Returns:
            ModelResponse with enhanced metadata
        """
        start_time = time.time()
        self._request_count += 1
        self._last_request_time = datetime.now()
        
        try:
            logger.debug(f"Generating response for prompt (length: {len(prompt)})")
            response = await self.generate(prompt, **kwargs)
            
            # Track successful generation
            response_time = time.time() - start_time
            self._total_response_time += response_time
            
            # Enhance response with tracking metadata
            if hasattr(response, 'response_time') and response.response_time is None:
                response.response_time = response_time
            if hasattr(response, 'model_name') and response.model_name is None:
                response.model_name = self.model_name
            if hasattr(response, 'prompt_length') and response.prompt_length is None:
                response.prompt_length = len(prompt)
            
            # Add performance metadata
            response.add_metadata('request_count', self._request_count)
            response.add_metadata('model_type', self.model_type)
            response.add_metadata('generation_timestamp', self._last_request_time.isoformat())
            
            logger.info(f"Generated response in {response_time:.2f}s (length: {len(response.text)})")
            return response
            
        except Exception as e:
            self._error_count += 1
            error_msg = f"Failed to generate response: {str(e)}"
            logger.error(error_msg)
            
            # Import here to avoid circular imports
            from .responses import ModelResponse
            return ModelResponse.create_error_response(
                error_message=error_msg,
                model_name=self.model_name,
                metadata={
                    'request_count': self._request_count,
                    'model_type': self.model_type,
                    'error_timestamp': datetime.now().isoformat(),
                    'prompt_length': len(prompt)
                }
            )
    
    async def batch_generate(
        self, 
        prompts: List[str], 
        **kwargs
    ) -> List["ModelResponse"]:
        """
        Generate responses for multiple prompts.
        
        Args:
            prompts: List of input prompts
            **kwargs: Additional arguments for generate()
            
        Returns:
            List of ModelResponse objects
        """
        logger.info(f"Starting batch generation for {len(prompts)} prompts")
        responses = []
        
        for i, prompt in enumerate(prompts):
            try:
                logger.debug(f"Processing prompt {i + 1}/{len(prompts)}")
                response = await self._generate_with_tracking(prompt, **kwargs)
                responses.append(response)
            except Exception as e:
                logger.error(f"Failed to process prompt {i + 1}: {str(e)}")
                # Import here to avoid circular imports
                from .responses import ModelResponse
                error_response = ModelResponse.create_error_response(
                    error_message=str(e),
                    model_name=self.model_name
                )
                responses.append(error_response)
        
        logger.info(f"Completed batch generation: {len(responses)} responses")
        return responses
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get performance and usage statistics.
        
        Returns:
            Dictionary with model statistics
        """
        avg_response_time = (
            self._total_response_time / max(self._request_count - self._error_count, 1)
            if self._request_count > self._error_count else 0
        )
        
        return {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'total_requests': self._request_count,
            'successful_requests': self._request_count - self._error_count,
            'failed_requests': self._error_count,
            'success_rate': (self._request_count - self._error_count) / max(self._request_count, 1),
            'average_response_time': avg_response_time,
            'total_response_time': self._total_response_time,
            'last_request_time': self._last_request_time.isoformat() if self._last_request_time else None,
            'is_available': self.is_available
        }
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self._request_count = 0
        self._error_count = 0
        self._total_response_time = 0.0
        self._last_request_time = None
        logger.info(f"Reset statistics for {self.model_name}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the model.
        
        Returns:
            Dictionary with health status
        """
        try:
            # Simple test generation
            start_time = time.time()
            test_response = await self.generate("Hello", max_tokens=5)
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'model_name': self.model_name,
                'response_time': response_time,
                'test_successful': test_response.is_successful,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'model_name': self.model_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}: {self.model_name}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        stats = self.get_stats()
        return (f"{self.__class__.__name__}(model_name='{self.model_name}', "
                f"requests={stats['total_requests']}, "
                f"success_rate={stats['success_rate']:.2%})") 