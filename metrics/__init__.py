"""
Metrics package for LLM benchmarking.

This package provides various metrics for evaluating LLM performance
organized by domain-specific subpackages.
"""

# Import from subpackages (optional - for backwards compatibility only)
# These are no longer needed - we use GenericMetric for all metrics
# Individual metric classes can be deleted
try:
    from .general import (
        RelevanceMetric, HallucinationsMetric, FairnessMetric,
        RobustnessMetric, BiasMetric, ToxicityMetric
    )
except ImportError:
    # Individual metric classes don't exist - that's fine, we use GenericMetric
    RelevanceMetric = HallucinationsMetric = FairnessMetric = None
    RobustnessMetric = BiasMetric = ToxicityMetric = None

try:
    from .email import (
        EmailProfessionalismMetric, EmailResponsivenessMetric,
        EmailClarityMetric, EmailEmpathyMetric
    )
except ImportError:
    EmailProfessionalismMetric = EmailResponsivenessMetric = None
    EmailClarityMetric = EmailEmpathyMetric = None

try:
    from .mcp import (
        ToolUsageAccuracyMetric, InformationRetrievalQualityMetric,
        ContextualAwarenessMetric, ToolSelectionEfficiencyMetric
    )
except ImportError:
    ToolUsageAccuracyMetric = InformationRetrievalQualityMetric = None
    ContextualAwarenessMetric = ToolSelectionEfficiencyMetric = None

# Base classes and utilities
from .metric_base import BaseMetric, StandardMetric
from .metric_factory import MetricFactory
from .evaluator import EvaluatorFactory
from .database_loader import load_metric_from_db, load_metrics_from_db, list_available_metrics_from_db

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
    'get_metric_by_name',
    # Database loading utilities (preferred for runtime)
    'load_metric_from_db',
    'load_metrics_from_db',
    'list_available_metrics_from_db',
    # RAG metrics
    'FaithfulnessMetric',
    'RAGRelevanceMetric',
    'LanguageQualityMetric',
    'GrammaticalCorrectnessMetric',
    'OverallRAGScoreMetric',
    'get_all_rag_metrics',
    'get_rag_metric_by_name'
]

# Import RAG metrics
try:
    from .rag_metrics import (
        FaithfulnessMetric, RelevanceMetric as RAGRelevanceMetric,
        LanguageQualityMetric, GrammaticalCorrectnessMetric,
        OverallRAGScoreMetric, get_all_rag_metrics, get_rag_metric_by_name,
        RAG_METRICS
    )
except ImportError:
    FaithfulnessMetric = RAGRelevanceMetric = LanguageQualityMetric = None
    GrammaticalCorrectnessMetric = OverallRAGScoreMetric = None
    get_all_rag_metrics = get_rag_metric_by_name = None
    RAG_METRICS = {}

# Metric registry - DEPRECATED
# NOTE: This registry is DEPRECATED. Individual metric classes are no longer needed.
# We use GenericMetric for all metrics, configured from the database.
# This registry is kept only for backwards compatibility with old code.
_METRIC_REGISTRY = {}
if RelevanceMetric:
    _METRIC_REGISTRY.update({
        'relevance': RelevanceMetric,
        'hallucinations': HallucinationsMetric,
        'fairness': FairnessMetric,
        'robustness': RobustnessMetric,
        'bias': BiasMetric,
        'toxicity': ToxicityMetric,
    })
if EmailProfessionalismMetric:
    _METRIC_REGISTRY.update({
        'email_professionalism': EmailProfessionalismMetric,
        'email_responsiveness': EmailResponsivenessMetric,
        'email_clarity': EmailClarityMetric,
        'email_empathy': EmailEmpathyMetric,
    })
if ToolUsageAccuracyMetric:
    _METRIC_REGISTRY.update({
        'tool_usage_accuracy': ToolUsageAccuracyMetric,
        'information_retrieval_quality': InformationRetrievalQualityMetric,
        'contextual_awareness': ContextualAwarenessMetric,
        'tool_selection_efficiency': ToolSelectionEfficiencyMetric,
    })

# Add RAG metrics to registry
if FaithfulnessMetric:
    _METRIC_REGISTRY.update({
        'faithfulness': FaithfulnessMetric,
        'rag_relevance': RAGRelevanceMetric,
        'language_quality': LanguageQualityMetric,
        'grammatical_correctness': GrammaticalCorrectnessMetric,
        'overall_rag_score': OverallRAGScoreMetric,
    })

def get_all_metrics():
    """Get all available metrics.
    
    DEPRECATED: Use list_available_metrics_from_db() instead to get metrics from database.
    """
    # Return hardcoded list for backwards compatibility
    return [
        'relevance', 'hallucinations', 'fairness', 'robustness', 'bias', 'toxicity',
        'email_professionalism', 'email_responsiveness', 'email_clarity', 'email_empathy',
        'tool_usage_accuracy', 'information_retrieval_quality', 'contextual_awareness', 'tool_selection_efficiency',
        'faithfulness', 'rag_relevance', 'language_quality', 'grammatical_correctness', 'overall_rag_score'
    ]

def get_metric_by_name(name: str):
    """Get a metric class by name.
    
    DEPRECATED: Use load_metrics_from_db() instead to load metrics from database.
    """
    return _METRIC_REGISTRY.get(name)

def get_metrics_by_category():
    """Get metrics organized by category."""
    return {
        'general': ['relevance', 'hallucinations', 'fairness', 'robustness', 'bias', 'toxicity'],
        'email': ['email_professionalism', 'email_responsiveness', 'email_clarity', 'email_empathy'],
        'mcp': ['tool_usage_accuracy', 'information_retrieval_quality', 'contextual_awareness', 'tool_selection_efficiency'],
        'rag': ['faithfulness', 'rag_relevance', 'language_quality', 'grammatical_correctness', 'overall_rag_score']
    }
