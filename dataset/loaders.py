"""
Dataset loaders for different file formats and input types.
"""

import json
import csv
import yaml
import os
from typing import List, Dict, Any, Union, Optional
from pathlib import Path
from .question import Question, QuestionCategory, QuestionDifficulty
from .dataset import Dataset


class DatasetLoader:
    """
    Flexible loader for creating datasets from various input sources.
    
    Supports loading from:
    - List of strings (simple prompts)
    - JSON files (structured question data)
    - CSV files (tabular question data) 
    - YAML files (structured question data)
    - Plain text files (one question per line)
    - Custom dictionary formats
    """
    
    @staticmethod
    def from_strings(
        prompts: List[str], 
        name: str = "String Dataset",
        description: str = "Dataset created from string list",
        **default_kwargs
    ) -> Dataset:
        """
        Create a dataset from a list of string prompts.
        
        Args:
            prompts: List of prompt strings
            name: Name for the dataset
            description: Description for the dataset
            **default_kwargs: Default properties for all questions
            
        Returns:
            Dataset instance
        """
        questions = []
        for i, prompt in enumerate(prompts):
            question = Question.from_string(
                text=prompt,
                id=default_kwargs.get('id_prefix', 'str') + f"_{i:04d}",
                **{k: v for k, v in default_kwargs.items() if k != 'id_prefix'}
            )
            questions.append(question)
        
        return Dataset(questions=questions, name=name, description=description)
    
    @staticmethod
    def from_json_file(filepath: str) -> Dataset:
        """
        Load dataset from a JSON file.
        
        Supports two formats:
        1. Direct Dataset JSON (from Dataset.to_json())
        2. Custom JSON with questions array
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Dataset instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if it's a direct Dataset JSON format
        if 'questions' in data and isinstance(data['questions'], list):
            if 'name' in data and 'description' in data:
                # This looks like a Dataset JSON
                return Dataset.from_dict(data)
            else:
                # This is a custom format with questions array
                return DatasetLoader._parse_custom_json(data, filepath)
        else:
            raise ValueError(f"Invalid JSON format in {filepath}. Expected format with 'questions' array.")
    
    @staticmethod
    def _parse_custom_json(data: Dict[str, Any], filepath: str) -> Dataset:
        """Parse custom JSON format."""
        questions = []
        
        for item in data['questions']:
            if isinstance(item, str):
                # Simple string format
                question = Question.from_string(item)
            elif isinstance(item, dict):
                # Dictionary format
                question = Question.from_dict(item)
            else:
                continue
            
            questions.append(question)
        
        # Extract metadata
        name = data.get('name', f"Dataset from {os.path.basename(filepath)}")
        description = data.get('description', f"Loaded from {filepath}")
        
        return Dataset(questions=questions, name=name, description=description)
    
    @staticmethod
    def from_csv_file(
        filepath: str,
        text_column: str = 'text',
        id_column: Optional[str] = None,
        category_column: Optional[str] = None,
        difficulty_column: Optional[str] = None,
        tags_column: Optional[str] = None,
        expected_answer_column: Optional[str] = None,
        context_column: Optional[str] = None,
        instructions_column: Optional[str] = None,
        delimiter: str = ',',
        **kwargs
    ) -> Dataset:
        """
        Load dataset from a CSV file.
        
        Args:
            filepath: Path to CSV file
            text_column: Name of column containing question text
            id_column: Name of column containing question IDs
            category_column: Name of column containing categories
            difficulty_column: Name of column containing difficulties
            tags_column: Name of column containing tags (comma-separated)
            expected_answer_column: Name of column containing expected answers
            context_column: Name of column containing context
            instructions_column: Name of column containing instructions
            delimiter: CSV delimiter
            **kwargs: Additional arguments for csv.DictReader
            
        Returns:
            Dataset instance
        """
        questions = []
        
        with open(filepath, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter=delimiter, **kwargs)
            
            for row_idx, row in enumerate(reader):
                # Required field
                if text_column not in row or not row[text_column].strip():
                    continue
                
                # Parse basic fields
                question_data = {
                    'text': row[text_column].strip(),
                    'id': row.get(id_column) if id_column else f"csv_{row_idx:04d}"
                }
                
                # Parse optional fields
                if category_column and row.get(category_column):
                    try:
                        question_data['category'] = QuestionCategory(row[category_column].lower())
                    except ValueError:
                        pass
                
                if difficulty_column and row.get(difficulty_column):
                    try:
                        question_data['difficulty'] = QuestionDifficulty(row[difficulty_column].lower())
                    except ValueError:
                        pass
                
                if tags_column and row.get(tags_column):
                    tags = [tag.strip() for tag in row[tags_column].split(',') if tag.strip()]
                    question_data['tags'] = tags
                
                if expected_answer_column and row.get(expected_answer_column):
                    question_data['expected_answer'] = row[expected_answer_column].strip()
                
                if context_column and row.get(context_column):
                    question_data['context'] = row[context_column].strip()
                
                if instructions_column and row.get(instructions_column):
                    question_data['instructions'] = row[instructions_column].strip()
                
                question = Question(**question_data)
                questions.append(question)
        
        name = f"Dataset from {os.path.basename(filepath)}"
        description = f"CSV dataset loaded from {filepath}"
        
        return Dataset(questions=questions, name=name, description=description)
    
    @staticmethod
    def from_yaml_file(filepath: str) -> Dataset:
        """
        Load dataset from a YAML file.
        
        Args:
            filepath: Path to YAML file
            
        Returns:
            Dataset instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Convert YAML to same format as JSON and reuse the JSON parser
        return DatasetLoader._parse_custom_json(data, filepath)
    
    @staticmethod
    def from_text_file(
        filepath: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        separator: str = '\n',
        **default_kwargs
    ) -> Dataset:
        """
        Load dataset from a plain text file.
        
        Args:
            filepath: Path to text file
            name: Name for the dataset
            description: Description for the dataset
            separator: Separator between questions (default: newline)
            **default_kwargs: Default properties for all questions
            
        Returns:
            Dataset instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by separator and filter empty lines
        prompts = [line.strip() for line in content.split(separator) if line.strip()]
        
        if name is None:
            name = f"Dataset from {os.path.basename(filepath)}"
        if description is None:
            description = f"Text dataset loaded from {filepath}"
        
        return DatasetLoader.from_strings(prompts, name=name, description=description, **default_kwargs)
    
    @staticmethod
    def from_dict_list(
        data: List[Dict[str, Any]], 
        name: str = "Dictionary Dataset",
        description: str = "Dataset created from dictionary list"
    ) -> Dataset:
        """
        Create a dataset from a list of dictionaries.
        
        Args:
            data: List of dictionaries containing question data
            name: Name for the dataset
            description: Description for the dataset
            
        Returns:
            Dataset instance
        """
        questions = []
        
        for item in data:
            if 'text' not in item:
                continue
            
            question = Question.from_dict(item)
            questions.append(question)
        
        return Dataset(questions=questions, name=name, description=description)
    
    @staticmethod
    def auto_load(
        input_data: Union[str, List[str], List[Dict[str, Any]], Dict[str, Any]],
        **kwargs
    ) -> Dataset:
        """
        Automatically detect input type and load accordingly.
        
        Args:
            input_data: Input data in various formats
            **kwargs: Additional arguments passed to specific loaders
            
        Returns:
            Dataset instance
        """
        if isinstance(input_data, str):
            # File path
            if os.path.isfile(input_data):
                return DatasetLoader.load_from_file(input_data, **kwargs)
            else:
                raise FileNotFoundError(f"File not found: {input_data}")
        
        elif isinstance(input_data, list):
            if not input_data:
                return Dataset(questions=[], name="Empty Dataset")
            
            # Check first item to determine type
            if isinstance(input_data[0], str):
                # List of strings
                return DatasetLoader.from_strings(input_data, **kwargs)
            elif isinstance(input_data[0], dict):
                # List of dictionaries
                return DatasetLoader.from_dict_list(input_data, **kwargs)
            else:
                raise ValueError(f"Unsupported list item type: {type(input_data[0])}")
        
        elif isinstance(input_data, dict):
            # Dictionary format
            if 'questions' in input_data:
                return DatasetLoader._parse_custom_json(input_data, "dictionary")
            else:
                raise ValueError("Dictionary must contain 'questions' key")
        
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
    
    @staticmethod
    def load_from_file(filepath: str, **kwargs) -> Dataset:
        """
        Load dataset from file, auto-detecting format.
        
        Args:
            filepath: Path to the file
            **kwargs: Additional arguments for specific loaders
            
        Returns:
            Dataset instance
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Get file extension
        ext = Path(filepath).suffix.lower()
        
        if ext == '.json':
            return DatasetLoader.from_json_file(filepath)
        elif ext == '.csv':
            return DatasetLoader.from_csv_file(filepath, **kwargs)
        elif ext in ['.yaml', '.yml']:
            return DatasetLoader.from_yaml_file(filepath)
        elif ext in ['.txt', '.text']:
            return DatasetLoader.from_text_file(filepath, **kwargs)
        else:
            # Try to detect format by content
            try:
                # Try JSON first
                return DatasetLoader.from_json_file(filepath)
            except (json.JSONDecodeError, ValueError):
                try:
                    # Try YAML
                    return DatasetLoader.from_yaml_file(filepath)
                except yaml.YAMLError:
                    # Fall back to text
                    return DatasetLoader.from_text_file(filepath, **kwargs)
    
    @staticmethod
    def create_sample_dataset() -> Dataset:
        """
        Create a sample dataset for testing and demonstration.
        
        Returns:
            Sample Dataset instance
        """
        questions = [
            Question(
                text="What is the capital of France?",
                category=QuestionCategory.FACTUAL,
                difficulty=QuestionDifficulty.EASY,
                tags=["geography", "capitals"],
                expected_answer="Paris",
                source="sample_generator"
            ),
            Question(
                text="Explain the concept of recursion in programming.",
                category=QuestionCategory.CODING,
                difficulty=QuestionDifficulty.MEDIUM,
                tags=["programming", "algorithms"],
                context="You are teaching a beginner programmer.",
                instructions="Provide a clear explanation with a simple example.",
                source="sample_generator"
            ),
            Question(
                text="Write a haiku about artificial intelligence.",
                category=QuestionCategory.CREATIVE,
                difficulty=QuestionDifficulty.MEDIUM,
                tags=["poetry", "ai", "creative"],
                instructions="Follow the traditional 5-7-5 syllable pattern.",
                source="sample_generator"
            ),
            Question(
                text="If you have 3 apples and give away 2, how many do you have left?",
                category=QuestionCategory.MATHEMATICAL,
                difficulty=QuestionDifficulty.EASY,
                tags=["arithmetic", "basic_math"],
                expected_answer="1",
                answer_key_points=["subtraction", "3 - 2 = 1"],
                source="sample_generator"
            ),
            Question(
                text="Analyze the ethical implications of autonomous vehicles in life-or-death scenarios.",
                category=QuestionCategory.ETHICAL,
                difficulty=QuestionDifficulty.EXPERT,
                tags=["ethics", "ai", "autonomous_vehicles", "philosophy"],
                context="Consider the trolley problem in the context of self-driving cars.",
                instructions="Discuss multiple perspectives and potential solutions.",
                source="sample_generator"
            )
        ]
        
        return Dataset(
            questions=questions,
            name="Sample Dataset",
            description="A diverse sample dataset for testing and demonstration purposes"
        ) 