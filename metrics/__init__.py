"""
Metrics module for LLM benchmarking.

This module provides evaluation metrics for assessing LLM responses.
"""

from typing import Dict, Type, List
from .metric_base import BaseMetric, StandardMetric
from .evaluator import BaseEvaluator, EvaluatorFactory
from .responses import (
    ModelResponse, 
    IndividualResponse, 
    EvaluatorResponse, 
    PromptEvaluation, 
    BenchmarkResult
)

# Import all metrics
from .relevance import RelevanceMetric
from .hallucinations import HallucinationsMetric
from .fairness import FairnessMetric
from .robustness import RobustnessMetric
from .bias import BiasMetric
from .toxicity import ToxicityMetric

# Import email-specific metrics
from .email_professionalism import EmailProfessionalismMetric
from .email_responsiveness import EmailResponsivenessMetric
from .email_clarity import EmailClarityMetric
from .email_empathy import EmailEmpathyMetric

__all__ = [
    # Base classes
    'BaseMetric',
    'StandardMetric', 
    'BaseEvaluator',
    'EvaluatorFactory',
    
    # Response classes
    'ModelResponse',
    'IndividualResponse',
    'EvaluatorResponse', 
    'PromptEvaluation',
    'BenchmarkResult',
    
    # Standard metrics
    'RelevanceMetric',
    'HallucinationsMetric',
    'FairnessMetric', 
    'RobustnessMetric',
    'BiasMetric',
    'ToxicityMetric',
    
    # Email-specific metrics
    'EmailProfessionalismMetric',
    'EmailResponsivenessMetric',
    'EmailClarityMetric',
    'EmailEmpathyMetric',
    
    # Utilities
    'MetricFactory',
    'get_all_metrics',
    'get_metric_by_name'
]

# Metric registry
_METRIC_REGISTRY = {
    'relevance': RelevanceMetric,
    'hallucinations': HallucinationsMetric,
    'fairness': FairnessMetric,
    'robustness': RobustnessMetric,
    'bias': BiasMetric,
    'toxicity': ToxicityMetric,
    'email_professionalism': EmailProfessionalismMetric,
    'email_responsiveness': EmailResponsivenessMetric,
    'email_clarity': EmailClarityMetric,
    'email_empathy': EmailEmpathyMetric
}

def get_all_metrics() -> Dict[str, Type[BaseMetric]]:
    """Get all available metrics."""
    return _METRIC_REGISTRY.copy()

def get_metric_by_name(name: str) -> Type[BaseMetric]:
    """Get a metric class by name."""
    if name not in _METRIC_REGISTRY:
        raise ValueError(f"Unknown metric: {name}. Available: {list(_METRIC_REGISTRY.keys())}")
    return _METRIC_REGISTRY[name]


class MetricFactory:
    """Factory for creating metric instances."""
    
    @staticmethod
    def create_metric(name: str, **kwargs) -> BaseMetric:
        """Create a metric instance by name."""
        metric_class = get_metric_by_name(name)
        return metric_class(**kwargs)
    
    @staticmethod
    def create_all_metrics() -> List[BaseMetric]:
        """Create instances of all available metrics."""
        return [metric_class() for metric_class in get_all_metrics().values()]
    
    @staticmethod
    def create_metrics_by_names(names: List[str]) -> List[BaseMetric]:
        """Create metric instances by names."""
        return [MetricFactory.create_metric(name) for name in names]
    
    @staticmethod
    def list_available_metrics() -> List[str]:
        """List all available metric names."""
        return list(_METRIC_REGISTRY.keys()) 