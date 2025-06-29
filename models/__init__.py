"""
Models module for LLM benchmarking.

This module provides LLM model wrappers and utilities for interacting with different LLM providers.
"""

from typing import Dict, Type, List, Union, Any
import logging
from .base_model import BaseLLMModel
from .model_config import OpenAIConfig, OllamaConfig
from .responses import ModelResponse

# Import all model implementations
from .openai_model import OpenAIModel
from .ollama_model import OllamaModel

# Set up logger for models
logger = logging.getLogger(__name__)

__all__ = [
    # Base classes
    'BaseLLMModel',
    'ModelResponse',
    
    # Configuration classes
    'OpenAIConfig',
    'OllamaConfig',
    
    # Model implementations
    'OpenAIModel',
    'OllamaModel',
    
    # Utilities
    'ModelFactory',
    'get_all_models',
    'get_model_by_name'
]

# Model registry
_MODEL_REGISTRY = {
    'openai': OpenAIModel,
    'ollama': OllamaModel,
}

# Configuration registry
_CONFIG_REGISTRY = {
    'openai': OpenAIConfig,
    'ollama': OllamaConfig,
}

def get_all_models() -> Dict[str, Type[BaseLLMModel]]:
    """Get all available model classes."""
    return _MODEL_REGISTRY.copy()

def get_model_by_name(name: str) -> Type[BaseLLMModel]:
    """
    Get a model class by name.
    
    Args:
        name: Name of the model type (e.g., 'openai', 'ollama')
        
    Returns:
        Model class
        
    Raises:
        ValueError: If model name is not found
    """
    name = name.lower()
    if name not in _MODEL_REGISTRY:
        available = list(_MODEL_REGISTRY.keys())
        raise ValueError(f"Unknown model type: {name}. Available: {available}")
    return _MODEL_REGISTRY[name]

def get_config_by_name(name: str) -> Type[Union[OpenAIConfig, OllamaConfig]]:
    """
    Get a configuration class by model name.
    
    Args:
        name: Name of the model type
        
    Returns:
        Configuration class
        
    Raises:
        ValueError: If model name is not found
    """
    name = name.lower()
    if name not in _CONFIG_REGISTRY:
        available = list(_CONFIG_REGISTRY.keys())
        raise ValueError(f"Unknown model type: {name}. Available: {available}")
    return _CONFIG_REGISTRY[name]


class ModelFactory:
    """Factory for creating model instances."""
    
    @staticmethod
    def create_model(model_type: str, config: Dict[str, Any] = None, **kwargs) -> BaseLLMModel:
        """
        Create a model instance by type.
        
        Args:
            model_type: Type of model ('openai', 'ollama')
            config: Configuration dictionary or None for defaults
            **kwargs: Additional configuration parameters
            
        Returns:
            Model instance
            
        Raises:
            ValueError: If invalid model type is provided
        """
        try:
            model_class = get_model_by_name(model_type)
            config_class = get_config_by_name(model_type)
            
            # Create configuration
            if config is None:
                config = {}
            config.update(kwargs)
            
            # Create config instance
            config_instance = config_class(**config)
            
            # Create model with config
            model = model_class(config=config_instance)
            
            logger.info(f"Created {model_type} model: {model.model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create {model_type} model: {str(e)}")
            raise ValueError(f"Failed to create {model_type} model: {str(e)}")
    
    @staticmethod
    def create_openai_model(
        model_name: str = "gpt-3.5-turbo",
        api_key: str = None,
        temperature: float = 0.7,
        **kwargs
    ) -> OpenAIModel:
        """
        Create an OpenAI model with convenient parameters.
        
        Args:
            model_name: OpenAI model name
            api_key: API key (optional if set in environment)
            temperature: Sampling temperature
            **kwargs: Additional configuration parameters
            
        Returns:
            OpenAI model instance
        """
        config_params = {
            'model_name': model_name,
            'temperature': temperature,
            **kwargs
        }
        if api_key:
            config_params['api_key'] = api_key
            
        return ModelFactory.create_model('openai', config_params)
    
    @staticmethod
    def create_ollama_model(
        model_name: str = "llama2",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        **kwargs
    ) -> OllamaModel:
        """
        Create an Ollama model with convenient parameters.
        
        Args:
            model_name: Ollama model name
            base_url: Ollama server URL
            temperature: Sampling temperature
            **kwargs: Additional configuration parameters
            
        Returns:
            Ollama model instance
        """
        config_params = {
            'model_name': model_name,
            'base_url': base_url,
            'temperature': temperature,
            **kwargs
        }
        
        return ModelFactory.create_model('ollama', config_params)
    
    @staticmethod
    def create_models_from_configs(configs: List[Dict[str, Any]]) -> List[BaseLLMModel]:
        """
        Create multiple models from configuration dictionaries.
        
        Args:
            configs: List of configuration dictionaries, each must contain 'type' key
            
        Returns:
            List of model instances
            
        Example:
            configs = [
                {'type': 'openai', 'model_name': 'gpt-4'},
                {'type': 'ollama', 'model_name': 'llama2', 'temperature': 0.5}
            ]
        """
        models = []
        for config in configs:
            if 'type' not in config:
                raise ValueError("Each config must contain 'type' key")
            
            model_type = config.pop('type')
            model = ModelFactory.create_model(model_type, config)
            models.append(model)
            
        logger.info(f"Created {len(models)} models from configurations")
        return models
    
    @staticmethod
    def list_available_models() -> List[str]:
        """List all available model types."""
        return list(_MODEL_REGISTRY.keys())
    
    @staticmethod
    def get_model_info(model_type: str) -> Dict[str, Any]:
        """
        Get information about a model type.
        
        Args:
            model_type: Type of model
            
        Returns:
            Dictionary with model information
        """
        model_class = get_model_by_name(model_type)
        config_class = get_config_by_name(model_type)
        
        return {
            'type': model_type,
            'class': model_class.__name__,
            'config_class': config_class.__name__,
            'description': model_class.__doc__ or "No description available"
        }
    
    @staticmethod
    def validate_model_config(model_type: str, config: Dict[str, Any]) -> bool:
        """
        Validate a configuration for a model type.
        
        Args:
            model_type: Type of model
            config: Configuration to validate
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        try:
            config_class = get_config_by_name(model_type)
            config_class(**config)
            return True
        except Exception as e:
            raise ValueError(f"Invalid configuration for {model_type}: {str(e)}") 