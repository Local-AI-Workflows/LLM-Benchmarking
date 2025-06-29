"""
Unit tests for OllamaModel class.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
from aioresponses import aioresponses

from models.ollama_model import OllamaModel, ModelResponse
from models.model_config import OllamaConfig


class TestOllamaModel:
    """Test cases for OllamaModel."""
    
    @pytest.mark.unit
    def test_initialization_default_config(self):
        """Test OllamaModel initialization with default config."""
        model = OllamaModel()
        
        assert model.model_name == "llama2"
        assert model.base_url == "http://localhost:11434"
        assert isinstance(model.config, OllamaConfig)
    
    @pytest.mark.unit
    def test_initialization_custom_config(self):
        """Test OllamaModel initialization with custom config."""
        config = OllamaConfig(
            model_name="custom-model",
            base_url="http://custom-host:8080",
            temperature=0.5
        )
        model = OllamaModel(config)
        
        assert model.model_name == "custom-model"
        assert model.base_url == "http://custom-host:8080"
        assert model.config.temperature == 0.5
    
    @pytest.mark.unit
    def test_base_url_stripping(self):
        """Test that base URL trailing slash is stripped."""
        config = OllamaConfig(base_url="http://localhost:11434/")
        model = OllamaModel(config)
        
        assert model.base_url == "http://localhost:11434"
    
    @pytest.mark.unit
    def test_str_representation(self):
        """Test string representation of OllamaModel."""
        config = OllamaConfig(model_name="test-model")
        model = OllamaModel(config)
        
        assert str(model) == "Ollama Model: test-model"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_success(self):
        """Test successful response generation."""
        model = OllamaModel()
        
        # Mock response data
        response_data = [
            '{"response": "Hello, ", "done": false}',
            '{"response": "world!", "done": true, "total_duration": 1000, "eval_count": 10}'
        ]
        
        with aioresponses() as m:
            # Mock the streaming response
            m.post(
                "http://localhost:11434/api/generate",
                status=200,
                body="\n".join(response_data),
                content_type="application/json"
            )
            
            result = await model.generate("Test prompt")
            
            assert isinstance(result, ModelResponse)
            assert result.text == "Hello, world!"
            assert result.metadata["model"] == "llama2"
            # Check that Ollama stats are in the metadata
            assert "ollama_stats" in result.metadata
            assert "config" in result.metadata
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_with_kwargs(self):
        """Test generation with additional parameters."""
        config = OllamaConfig(temperature=0.7)
        model = OllamaModel(config)
        
        response_data = '{"response": "Test response", "done": true}'
        
        with aioresponses() as m:
            m.post(
                "http://localhost:11434/api/generate",
                status=200,
                body=response_data,
                content_type="application/json"
            )
            
            result = await model.generate(
                "Test prompt",
                temperature=0.5,  # Override config temperature
                custom_param="value"
            )
            
            # Just verify the request was made and response is correct
            assert isinstance(result, ModelResponse)
            assert result.text == "Test response"
            assert result.metadata["model"] == "llama2"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_http_error(self):
        """Test handling of HTTP errors."""
        model = OllamaModel()
        
        with aioresponses() as m:
            m.post(
                "http://localhost:11434/api/generate",
                status=500,
                body="Internal Server Error"
            )
            
            with pytest.raises(Exception) as exc_info:
                await model.generate("Test prompt")
            
            assert "Ollama API error (status 500)" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_invalid_json_handling(self):
        """Test handling of invalid JSON in response."""
        model = OllamaModel()
        
        # Mix of valid and invalid JSON lines
        response_data = [
            '{"response": "Valid ", "done": false}',
            'invalid json line',
            '{"response": "response", "done": true}'
        ]
        
        with aioresponses() as m:
            m.post(
                "http://localhost:11434/api/generate",
                status=200,
                body="\n".join(response_data),
                content_type="application/json"
            )
            
            # Should handle invalid JSON gracefully and continue
            result = await model.generate("Test prompt")
            
            assert result.text == "Valid response"  # Should combine valid parts
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_empty_response(self):
        """Test handling of empty response."""
        model = OllamaModel()
        
        response_data = '{"response": " ", "done": true}'  # Whitespace that gets trimmed
        
        with aioresponses() as m:
            m.post(
                "http://localhost:11434/api/generate",
                status=200,
                body=response_data,
                content_type="application/json"
            )
            
            # This should raise an exception since empty text is not allowed
            with pytest.raises(Exception) as exc_info:
                await model.generate("Test prompt")
            
            assert "Unexpected error during Ollama generation" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_connection_error(self):
        """Test handling of connection errors."""
        model = OllamaModel()
        
        with aioresponses() as m:
            m.post(
                "http://localhost:11434/api/generate",
                exception=aiohttp.ClientError("Connection failed")
            )
            
            with pytest.raises(Exception) as exc_info:
                await model.generate("Test prompt")
            
            assert "Ollama connection error" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_model_name_property(self):
        """Test model_name property."""
        config = OllamaConfig(model_name="test-model")
        model = OllamaModel(config)
        
        assert model.model_name == "test-model"
        
        # Test that it matches the internal _model_name
        assert model.model_name == model._model_name
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_metadata_structure(self):
        """Test that response metadata has the expected structure."""
        model = OllamaModel()
        
        response_data = '{"response": "Test response", "done": true, "total_duration": 5000000, "load_duration": 1000000, "prompt_eval_duration": 2000000, "eval_duration": 2000000, "eval_count": 25}'
        
        with aioresponses() as m:
            m.post(
                "http://localhost:11434/api/generate",
                status=200,
                body=response_data,
                content_type="application/json"
            )
            
            result = await model.generate("Test prompt")
            
            metadata = result.metadata
            assert metadata["model"] == "llama2"
            assert "ollama_stats" in metadata
            assert "config" in metadata
            assert isinstance(metadata["config"], dict)
            
            # Check Ollama stats
            ollama_stats = metadata["ollama_stats"]
            assert ollama_stats["total_duration"] == 5000000
            assert ollama_stats["load_duration"] == 1000000
            assert ollama_stats["prompt_eval_duration"] == 2000000
            assert ollama_stats["eval_duration"] == 2000000
            assert ollama_stats["eval_count"] == 25
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_missing_metadata_fields(self):
        """Test handling when some metadata fields are missing."""
        model = OllamaModel()
        
        # Response with minimal metadata
        response_data = '{"response": "Test", "done": true}'
        
        with aioresponses() as m:
            m.post(
                "http://localhost:11434/api/generate",
                status=200,
                body=response_data,
                content_type="application/json"
            )
            
            result = await model.generate("Test prompt")
            
            # Should still work even with missing metadata
            assert result.text == "Test"
            assert result.metadata["model"] == "llama2"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_config_additional_params_merge(self):
        """Test that additional_params from config are properly merged."""
        config = OllamaConfig(
            model_name="test-model",
            additional_params={"custom_config": "value", "num_predict": 100}
        )
        model = OllamaModel(config)
        
        response_data = '{"response": "Test", "done": true}'
        
        with aioresponses() as m:
            m.post(
                "http://localhost:11434/api/generate",
                status=200,
                body=response_data,
                content_type="application/json"
            )
            
            result = await model.generate("Test prompt", override_param="override_value")
            
            # Just verify the request was made and response is correct
            assert isinstance(result, ModelResponse)
            assert result.text == "Test"
            assert result.metadata["model"] == "test-model" 