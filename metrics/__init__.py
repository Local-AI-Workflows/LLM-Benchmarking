"""
Metrics package for LLM benchmarking.

This package provides various metrics for evaluating LLM performance
organized by domain-specific subpackages.
"""

# Import from subpackages
from .general import (
    RelevanceMetric, HallucinationsMetric, FairnessMetric,
    RobustnessMetric, BiasMetric, ToxicityMetric
)
from .email import (
    EmailProfessionalismMetric, EmailResponsivenessMetric,
    EmailClarityMetric, EmailEmpathyMetric
)
from .mcp import (
    ToolUsageAccuracyMetric, InformationRetrievalQualityMetric,
    ContextualAwarenessMetric, ToolSelectionEfficiencyMetric
)

# Base classes and utilities
from .metric_base import BaseMetric, StandardMetric
from .metric_factory import MetricFactory
from .evaluator import EvaluatorFactory

__all__ = [
    # Base classes
    'BaseMetric',
    'StandardMetric',
    
    # General metrics
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

    # MCP-specific metrics
    'ToolUsageAccuracyMetric',
    'InformationRetrievalQualityMetric',
    'ContextualAwarenessMetric',
    'ToolSelectionEfficiencyMetric',

    # Utilities
    'MetricFactory',
    'EvaluatorFactory',
    'get_all_metrics',
    'get_metric_by_name'
]

# Metric registry - organized by category
_METRIC_REGISTRY = {
    # General metrics
    'relevance': RelevanceMetric,
    'hallucinations': HallucinationsMetric,
    'fairness': FairnessMetric,
    'robustness': RobustnessMetric,
    'bias': BiasMetric,
    'toxicity': ToxicityMetric,
    
    # Email metrics
    'email_professionalism': EmailProfessionalismMetric,
    'email_responsiveness': EmailResponsivenessMetric,
    'email_clarity': EmailClarityMetric,
    'email_empathy': EmailEmpathyMetric,
    
    # MCP metrics
    'tool_usage_accuracy': ToolUsageAccuracyMetric,
    'information_retrieval_quality': InformationRetrievalQualityMetric,
    'contextual_awareness': ContextualAwarenessMetric,
    'tool_selection_efficiency': ToolSelectionEfficiencyMetric,
}

def get_all_metrics():
    """Get all available metrics."""
    return list(_METRIC_REGISTRY.keys())

def get_metric_by_name(name: str):
    """Get a metric class by name."""
    return _METRIC_REGISTRY.get(name)

def get_metrics_by_category():
    """Get metrics organized by category."""
    return {
        'general': ['relevance', 'hallucinations', 'fairness', 'robustness', 'bias', 'toxicity'],
        'email': ['email_professionalism', 'email_responsiveness', 'email_clarity', 'email_empathy'],
        'mcp': ['tool_usage_accuracy', 'information_retrieval_quality', 'contextual_awareness', 'tool_selection_efficiency']
    }
