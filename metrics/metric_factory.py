"""Factory for creating metric instances."""

from typing import List, Type
from .metric_base import BaseMetric


class MetricFactory:
    """Factory for creating metric instances."""
    
    @staticmethod
    def create_metric(name: str, **kwargs) -> BaseMetric:
        """Create a metric instance by name."""
        from . import get_metric_by_name
        metric_class = get_metric_by_name(name)
        if metric_class is None:
            from . import get_all_metrics
            raise ValueError(f"Unknown metric: {name}. Available: {get_all_metrics()}")
        return metric_class(**kwargs)
    
    @staticmethod
    def create_all_metrics() -> List[BaseMetric]:
        """Create instances of all available metrics."""
        from . import _METRIC_REGISTRY
        return [metric_class() for metric_class in _METRIC_REGISTRY.values()]
    
    @staticmethod
    def create_metrics_by_names(names: List[str]) -> List[BaseMetric]:
        """Create metric instances by names."""
        return [MetricFactory.create_metric(name) for name in names]
    
    @staticmethod
    def list_available_metrics() -> List[str]:
        """List all available metric names."""
        from . import get_all_metrics
        return get_all_metrics()
    
    @staticmethod
    def get_metrics_by_category(category: str) -> List[str]:
        """Get metric names for a specific category."""
        from . import get_metrics_by_category
        return get_metrics_by_category().get(category, []) 