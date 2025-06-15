from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

from .evaluator import BaseEvaluator


class MetricResult(BaseModel):
    """Container for metric evaluation results."""
    score: float
    rationale: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseMetric(ABC):
    """Base class for all metrics in the benchmarking system."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator) -> MetricResult:
        """
        Evaluate a response against a prompt using this metric.
        
        Args:
            prompt: The input prompt
            response: The model's response
            evaluator: The evaluator to use for evaluation

        Returns:
            MetricResult containing the score and optional rationale
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}" 