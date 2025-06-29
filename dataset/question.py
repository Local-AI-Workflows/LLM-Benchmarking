"""
Question data structures for LLM benchmarking.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import json


@dataclass
class Question:
    """
    Representation of a test question.
    
    This class provides a structure for test questions that goes beyond
    simple strings, including metadata and expected answer information.
    """
    
    # Core question data
    text: str
    id: Optional[str] = None
    
    # Expected answer information (optional)
    expected_answer: Optional[str] = None
    reference_answers: List[str] = field(default_factory=list)
    answer_key_points: List[str] = field(default_factory=list)
    
    # Context and instructions
    context: Optional[str] = None
    instructions: Optional[str] = None
    
    # Metadata
    source: Optional[str] = None
    author: Optional[str] = None
    language: str = "en"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.id is None:
            # Generate a simple ID based on text hash if not provided
            self.id = f"q_{hash(self.text) % 1000000:06d}"
    
    def get_full_prompt(self) -> str:
        """
        Generate the complete prompt text including context and instructions.
        
        Returns:
            The full prompt text to be used for evaluation
        """
        parts = []
        
        if self.context:
            parts.append(f"Context: {self.context}")
        
        if self.instructions:
            parts.append(f"Instructions: {self.instructions}")
        
        parts.append(self.text)
        
        return "\n\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the question to a dictionary representation.
        
        Returns:
            Dictionary representation of the question
        """
        return {
            "id": self.id,
            "text": self.text,
            "expected_answer": self.expected_answer,
            "reference_answers": self.reference_answers,
            "answer_key_points": self.answer_key_points,
            "context": self.context,
            "instructions": self.instructions,
            "source": self.source,
            "author": self.author,
            "language": self.language,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        """
        Create a Question instance from a dictionary.
        
        Args:
            data: Dictionary containing question data
            
        Returns:
            Question instance
        """
        return cls(
            id=data.get("id"),
            text=data["text"],
            expected_answer=data.get("expected_answer"),
            reference_answers=data.get("reference_answers", []),
            answer_key_points=data.get("answer_key_points", []),
            context=data.get("context"),
            instructions=data.get("instructions"),
            source=data.get("source"),
            author=data.get("author"),
            language=data.get("language", "en"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_string(cls, text: str, **kwargs) -> 'Question':
        """
        Create a Question instance from a simple string.
        
        Args:
            text: The question text
            **kwargs: Additional properties to set
            
        Returns:
            Question instance
        """
        return cls(text=text, **kwargs)
    
    def to_json(self) -> str:
        """
        Convert the question to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Question':
        """
        Create a Question instance from JSON string.
        
        Args:
            json_str: JSON string containing question data
            
        Returns:
            Question instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value."""
        return self.metadata.get(key, default)
    
    def __str__(self) -> str:
        """String representation of the question."""
        return f"Question(id={self.id}, text='{self.text[:50]}...')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the question."""
        return f"Question(id={self.id!r}, text={self.text!r})" 