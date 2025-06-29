"""
Dataset package for LLM benchmarking.

This package provides data structures and loaders for handling test questions and datasets.
"""

from .question import Question, QuestionCategory, QuestionDifficulty
from .dataset import Dataset
from .loaders import DatasetLoader

__all__ = [
    'Question',
    'QuestionCategory', 
    'QuestionDifficulty',
    'Dataset',
    'DatasetLoader'
] 