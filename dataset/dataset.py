"""
Dataset class for managing collections of questions.
"""

from typing import List, Dict, Any, Optional, Iterator, Callable
from collections import Counter
import json
import random
from .question import Question


class Dataset:
    """
    Collection of questions with management and filtering capabilities.
    """
    
    def __init__(self, questions: List[Question] = None, name: str = None, description: str = None):
        """
        Initialize the dataset.
        
        Args:
            questions: Initial list of questions
            name: Name of the dataset
            description: Description of the dataset
        """
        self.questions: List[Question] = questions or []
        self.name = name or "Unnamed Dataset"
        self.description = description or ""
        self.metadata: Dict[str, Any] = {}
    
    def add_question(self, question: Question) -> None:
        """Add a question to the dataset."""
        self.questions.append(question)
    
    def add_questions(self, questions: List[Question]) -> None:
        """Add multiple questions to the dataset."""
        self.questions.extend(questions)
    
    def remove_question(self, question_id: str) -> bool:
        """
        Remove a question by ID.
        
        Args:
            question_id: ID of the question to remove
            
        Returns:
            True if question was found and removed, False otherwise
        """
        for i, question in enumerate(self.questions):
            if question.id == question_id:
                del self.questions[i]
                return True
        return False
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """
        Get a question by ID.
        
        Args:
            question_id: ID of the question to retrieve
            
        Returns:
            Question if found, None otherwise
        """
        for question in self.questions:
            if question.id == question_id:
                return question
        return None
    
    def filter_questions(
        self,
        custom_filter: Optional[Callable[[Question], bool]] = None,
        text_contains: Optional[str] = None
    ) -> 'Dataset':
        """
        Filter questions based on criteria and return a new dataset.
        
        Args:
            custom_filter: Custom filter function
            text_contains: Filter by text content (case-insensitive)
            
        Returns:
            New Dataset containing filtered questions
        """
        filtered_questions = []
        
        for question in self.questions:
            # Check text content filter
            if text_contains and text_contains.lower() not in question.text.lower():
                continue
            
            # Check custom filter
            if custom_filter and not custom_filter(question):
                continue
            
            filtered_questions.append(question)
        
        return Dataset(
            questions=filtered_questions,
            name=f"{self.name} (Filtered)",
            description=f"Filtered from: {self.description}"
        )
    
    def sample(self, n: int, random_seed: Optional[int] = None) -> 'Dataset':
        """
        Get a random sample of questions.
        
        Args:
            n: Number of questions to sample
            random_seed: Random seed for reproducible sampling
            
        Returns:
            New Dataset containing sampled questions
        """
        if random_seed is not None:
            random.seed(random_seed)
        
        sample_size = min(n, len(self.questions))
        sampled_questions = random.sample(self.questions, sample_size)
        
        return Dataset(
            questions=sampled_questions,
            name=f"{self.name} (Sample {sample_size})",
            description=f"Random sample from: {self.description}"
        )
    
    def shuffle(self, random_seed: Optional[int] = None) -> 'Dataset':
        """
        Return a new dataset with shuffled questions.
        
        Args:
            random_seed: Random seed for reproducible shuffling
            
        Returns:
            New Dataset with shuffled questions
        """
        if random_seed is not None:
            random.seed(random_seed)
        
        shuffled_questions = self.questions.copy()
        random.shuffle(shuffled_questions)
        
        return Dataset(
            questions=shuffled_questions,
            name=self.name,
            description=self.description
        )
    
    def split(self, train_ratio: float = 0.8, random_seed: Optional[int] = None) -> tuple['Dataset', 'Dataset']:
        """
        Split the dataset into train and test sets.
        
        Args:
            train_ratio: Ratio of questions for training set
            random_seed: Random seed for reproducible splitting
            
        Returns:
            Tuple of (train_dataset, test_dataset)
        """
        if random_seed is not None:
            random.seed(random_seed)
        
        shuffled_questions = self.questions.copy()
        random.shuffle(shuffled_questions)
        
        split_index = int(len(shuffled_questions) * train_ratio)
        train_questions = shuffled_questions[:split_index]
        test_questions = shuffled_questions[split_index:]
        
        train_dataset = Dataset(
            questions=train_questions,
            name=f"{self.name} (Train)",
            description=f"Training split from: {self.description}"
        )
        
        test_dataset = Dataset(
            questions=test_questions,
            name=f"{self.name} (Test)",
            description=f"Test split from: {self.description}"
        )
        
        return train_dataset, test_dataset
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the dataset.
        
        Returns:
            Dictionary containing dataset statistics
        """
        stats = {
            "total_questions": len(self.questions),
            "languages": {},
            "has_expected_answers": 0,
            "has_context": 0,
            "has_instructions": 0,
            "average_text_length": 0
        }
        
        if not self.questions:
            return stats
        
        # Count languages
        language_counts = Counter(q.language for q in self.questions)
        stats["languages"] = dict(language_counts)
        
        # Count optional fields
        stats["has_expected_answers"] = sum(1 for q in self.questions if q.expected_answer)
        stats["has_context"] = sum(1 for q in self.questions if q.context)
        stats["has_instructions"] = sum(1 for q in self.questions if q.instructions)
        
        # Calculate average text length
        total_length = sum(len(q.text) for q in self.questions)
        stats["average_text_length"] = total_length / len(self.questions)
        
        return stats
    
    def to_prompts(self) -> List[str]:
        """
        Convert all questions to prompt strings.
        
        Returns:
            List of prompt strings
        """
        return [question.get_full_prompt() for question in self.questions]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the dataset to a dictionary representation.
        
        Returns:
            Dictionary representation of the dataset
        """
        return {
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "questions": [question.to_dict() for question in self.questions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dataset':
        """
        Create a Dataset instance from a dictionary.
        
        Args:
            data: Dictionary containing dataset data
            
        Returns:
            Dataset instance
        """
        questions = [Question.from_dict(q_data) for q_data in data.get("questions", [])]
        
        dataset = cls(
            questions=questions,
            name=data.get("name"),
            description=data.get("description")
        )
        dataset.metadata = data.get("metadata", {})
        
        return dataset
    
    def to_json(self) -> str:
        """
        Convert the dataset to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Dataset':
        """
        Create a Dataset instance from JSON string.
        
        Args:
            json_str: JSON string containing dataset data
            
        Returns:
            Dataset instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save the dataset to a JSON file.
        
        Args:
            filepath: Path where to save the file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'Dataset':
        """
        Load a dataset from a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            Dataset instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            json_str = f.read()
        return cls.from_json(json_str)
    
    def __len__(self) -> int:
        """Return the number of questions in the dataset."""
        return len(self.questions)
    
    def __iter__(self) -> Iterator[Question]:
        """Iterate over questions in the dataset."""
        return iter(self.questions)
    
    def __getitem__(self, index: int) -> Question:
        """Get a question by index."""
        return self.questions[index]
    
    def __str__(self) -> str:
        """String representation of the dataset."""
        return f"Dataset(name='{self.name}', questions={len(self.questions)})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the dataset."""
        return f"Dataset(name={self.name!r}, description={self.description!r}, questions={len(self.questions)})" 