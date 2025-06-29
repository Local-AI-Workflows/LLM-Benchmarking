"""
Response objects for LLM model interactions.

This module provides Pydantic-based response objects with validation and enhanced metadata tracking.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
import logging
from datetime import datetime

# Set up logger for responses
logger = logging.getLogger(__name__)


class ModelResponse(BaseModel):
    """
    Enhanced container for model responses with validation and metadata.
    
    This class uses Pydantic for automatic validation and serialization.
    """
    text: str = Field(..., min_length=1, description="Generated text response")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    
    # Enhanced metadata fields
    model_name: Optional[str] = Field(None, description="Name of the model that generated the response")
    response_time: Optional[float] = Field(None, ge=0, description="Response generation time in seconds")
    token_count: Optional[int] = Field(None, ge=0, description="Number of tokens in response")
    prompt_length: Optional[int] = Field(None, ge=0, description="Length of input prompt")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response generation timestamp")
    
    # API-specific metadata
    finish_reason: Optional[str] = Field(None, description="Reason why generation finished")
    usage_stats: Dict[str, Any] = Field(default_factory=dict, description="Token usage statistics")
    
    # Error handling
    error: Optional[str] = Field(None, description="Error message if generation failed")
    is_successful: bool = Field(True, description="Whether response generation was successful")
    
    @validator('text')
    def validate_text(cls, v):
        """Validate that text is not empty and strip whitespace."""
        if not v or not v.strip():
            raise ValueError("Response text cannot be empty")
        return v.strip()
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Ensure metadata is a dictionary."""
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v
    
    @validator('response_time')
    def validate_response_time(cls, v):
        """Validate response time is positive."""
        if v is not None and v < 0:
            raise ValueError("Response time must be non-negative")
        return v
    
    @validator('token_count')
    def validate_token_count(cls, v):
        """Validate token count is positive."""
        if v is not None and v < 0:
            raise ValueError("Token count must be non-negative")
        return v
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata entry."""
        self.metadata[key] = value
        logger.debug(f"Added metadata: {key} = {value}")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value with optional default."""
        return self.metadata.get(key, default)
    
    def update_usage_stats(self, stats: Dict[str, Any]) -> None:
        """Update usage statistics."""
        self.usage_stats.update(stats)
        logger.debug(f"Updated usage stats: {stats}")
    
    def mark_as_error(self, error_message: str) -> None:
        """Mark response as failed with error message."""
        self.error = error_message
        self.is_successful = False
        logger.error(f"Response marked as error: {error_message}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the response."""
        return {
            'text_length': len(self.text),
            'model_name': self.model_name,
            'response_time': self.response_time,
            'token_count': self.token_count,
            'is_successful': self.is_successful,
            'finish_reason': self.finish_reason,
            'timestamp': self.timestamp.isoformat(),
            'has_error': self.error is not None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = self.dict()
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelResponse':
        """Create ModelResponse from dictionary."""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    @classmethod
    def create_error_response(
        cls, 
        error_message: str, 
        model_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ModelResponse':
        """
        Create an error response.
        
        Args:
            error_message: Description of the error
            model_name: Name of the model that failed
            metadata: Additional metadata
            
        Returns:
            ModelResponse marked as error
        """
        response = cls(
            text="[ERROR: Response generation failed]",
            model_name=model_name,
            metadata=metadata or {},
            is_successful=False,
            error=error_message
        )
        logger.error(f"Created error response: {error_message}")
        return response
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 