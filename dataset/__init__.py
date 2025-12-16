"""
Dataset package for LLM benchmarking.

This package provides data structures and loaders for handling test questions and datasets.
"""

from .question import Question
from .dataset import Dataset
from .loaders import DatasetLoader
from .email_loader import EmailDatasetLoader

__all__ = [
    'Question',
    'Dataset',
    'DatasetLoader',
    'EmailDatasetLoader'
] 