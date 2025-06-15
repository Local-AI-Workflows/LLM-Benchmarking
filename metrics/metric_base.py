from abc import ABC, abstractmethod
from typing import Dict, Any

from .evaluator import BaseEvaluator
from .responses import EvaluatorResponse


class BaseMetric(ABC):
    """Base class for all metrics in the benchmarking system."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator) -> EvaluatorResponse:
        """
        Evaluate a response against a prompt using this metric.
        
        Args:
            prompt: The input prompt
            response: The model's response
            evaluator: The evaluator to use for evaluation

        Returns:
            EvaluatorResponse containing the evaluation results
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}" 