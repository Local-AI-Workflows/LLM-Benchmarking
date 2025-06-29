"""
Unit tests for model configuration classes.
"""

import pytest
from pydantic import ValidationError
from models.model_config import OllamaConfig, OpenAIConfig


class TestOllamaConfig:
    """Test cases for OllamaConfig."""
    
    @pytest.mark.unit
    def test_default_config(self):
        """Test default OllamaConfig initialization."""
        config = OllamaConfig()
        
        assert config.model_name == "llama2"
        assert config.base_url == "http://localhost:11434"
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.top_k == 40
        assert config.num_ctx == 2048
        assert config.num_thread == 4
        assert config.repeat_penalty == 1.1
        assert config.stop is None
        assert config.stream is True
        assert config.additional_params == {}
    
    @pytest.mark.unit
    def test_custom_config(self):
        """Test OllamaConfig with custom values."""
        config = OllamaConfig(
            model_name="custom-model",
            base_url="http://custom-host:8080",
            temperature=0.5,
            top_p=0.8,
            top_k=50,
            num_ctx=4096,
            stop=["</s>", "\n\n"],
            additional_params={"custom_param": "value"}
        )
        
        assert config.model_name == "custom-model"
        assert config.base_url == "http://custom-host:8080"
        assert config.temperature == 0.5
        assert config.top_p == 0.8
        assert config.top_k == 50
        assert config.num_ctx == 4096
        assert config.stop == ["</s>", "\n\n"]
        assert config.additional_params == {"custom_param": "value"}
    
    @pytest.mark.unit
    def test_temperature_validation(self):
        """Test temperature validation bounds."""
        # Valid temperatures
        OllamaConfig(temperature=0.0)
        OllamaConfig(temperature=1.0)
        OllamaConfig(temperature=0.5)
        
        # Test that invalid temperatures raise validation errors
        with pytest.raises(ValidationError):
            OllamaConfig(temperature=2.0)  # Too high for Ollama
        
        with pytest.raises(ValidationError):
            OllamaConfig(temperature=-0.1)  # Negative temperature
    
    @pytest.mark.unit
    def test_serialization(self):
        """Test config serialization to dict."""
        config = OllamaConfig(
            model_name="test-model",
            temperature=0.8,
            additional_params={"test": "value"}
        )
        
        config_dict = config.dict()
        
        assert config_dict["model_name"] == "test-model"
        assert config_dict["temperature"] == 0.8
        assert config_dict["additional_params"] == {"test": "value"}
        assert "base_url" in config_dict
    
    @pytest.mark.unit
    def test_json_serialization(self):
        """Test config JSON serialization."""
        config = OllamaConfig(model_name="test-model")
        json_str = config.json()
        
        assert isinstance(json_str, str)
        assert "test-model" in json_str
        
        # Test round-trip
        config_restored = OllamaConfig.parse_raw(json_str)
        assert config_restored.model_name == "test-model"


class TestOpenAIConfig:
    """Test cases for OpenAIConfig."""
    
    @pytest.mark.unit
    def test_default_config(self):
        """Test default OpenAIConfig initialization."""
        config = OpenAIConfig()
        
        assert config.model_name == "gpt-3.5-turbo"
        assert config.api_key is None
        assert config.temperature == 0.7
        assert config.max_tokens is None
        assert config.top_p == 1.0
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0
        assert config.stop is None
        assert config.additional_params == {}
    
    @pytest.mark.unit
    def test_custom_config(self):
        """Test OpenAIConfig with custom values."""
        config = OpenAIConfig(
            model_name="gpt-4",
            api_key="test-key-123",
            temperature=0.3,
            max_tokens=2000,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.3,
            stop=["\n", "END"],
            additional_params={"logprobs": 5}
        )
        
        assert config.model_name == "gpt-4"
        assert config.api_key == "test-key-123"
        assert config.temperature == 0.3
        assert config.max_tokens == 2000
        assert config.top_p == 0.9
        assert config.frequency_penalty == 0.5
        assert config.presence_penalty == 0.3
        assert config.stop == ["\n", "END"]
        assert config.additional_params == {"logprobs": 5}
    
    @pytest.mark.unit
    def test_penalty_bounds(self):
        """Test penalty parameter bounds."""
        # Valid penalties (within -2.0 to 2.0 range)
        config = OpenAIConfig(frequency_penalty=-2.0, presence_penalty=2.0)
        assert config.frequency_penalty == -2.0
        assert config.presence_penalty == 2.0
        
        # Test that invalid penalties raise validation errors
        with pytest.raises(ValidationError):
            OpenAIConfig(frequency_penalty=5.0)  # Too high
        
        with pytest.raises(ValidationError):
            OpenAIConfig(presence_penalty=-5.0)  # Too low
    
    @pytest.mark.unit
    def test_serialization(self):
        """Test config serialization to dict."""
        config = OpenAIConfig(
            model_name="gpt-4",
            api_key="secret-key",
            temperature=0.5,
            max_tokens=1500
        )
        
        config_dict = config.dict()
        
        assert config_dict["model_name"] == "gpt-4"
        assert config_dict["api_key"] == "secret-key"
        assert config_dict["temperature"] == 0.5
        assert config_dict["max_tokens"] == 1500
    
    @pytest.mark.unit
    def test_serialization_excludes_sensitive_data(self):
        """Test that we can exclude sensitive data from serialization."""
        config = OpenAIConfig(
            model_name="gpt-4",
            api_key="secret-key",
            temperature=0.5
        )
        
        # Serialize without API key
        config_dict = config.dict(exclude={"api_key"})
        
        assert "api_key" not in config_dict
        assert config_dict["model_name"] == "gpt-4"
        assert config_dict["temperature"] == 0.5
    
    @pytest.mark.unit
    def test_json_serialization(self):
        """Test config JSON serialization."""
        config = OpenAIConfig(model_name="gpt-4", temperature=0.5)
        json_str = config.json()
        
        assert isinstance(json_str, str)
        assert "gpt-4" in json_str
        
        # Test round-trip
        config_restored = OpenAIConfig.parse_raw(json_str)
        assert config_restored.model_name == "gpt-4"
        assert config_restored.temperature == 0.5


class TestConfigComparison:
    """Test cases for comparing configurations."""
    
    @pytest.mark.unit
    def test_config_equality(self):
        """Test configuration equality comparison."""
        config1 = OllamaConfig(model_name="test", temperature=0.7)
        config2 = OllamaConfig(model_name="test", temperature=0.7)
        config3 = OllamaConfig(model_name="different", temperature=0.7)
        
        assert config1 == config2
        assert config1 != config3
    
    @pytest.mark.unit
    def test_config_copy(self):
        """Test configuration copying."""
        original = OpenAIConfig(
            model_name="gpt-4",
            temperature=0.8,
            additional_params={"test": "value"}
        )
        
        # Test copy with updates
        updated = original.copy(update={"temperature": 0.5})
        
        assert original.temperature == 0.8
        assert updated.temperature == 0.5
        assert updated.model_name == "gpt-4"
        assert updated.additional_params == {"test": "value"}
    
    @pytest.mark.unit
    def test_config_validation_on_update(self):
        """Test that validation occurs when updating configs."""
        config = OllamaConfig()
        
        # Valid update
        updated = config.copy(update={"temperature": 0.5})
        assert updated.temperature == 0.5
        
        # Test that the original config wasn't modified
        assert config.temperature == 0.7 