"""Generic metric classes that are configured entirely from the database.

These classes can be used for any metric type - no need to create individual
metric classes. All configuration comes from the database.
"""

from .metric_base import StandardMetric, BaseMetric
from typing import Optional


class GenericMetric(StandardMetric):
    """
    Generic metric class that can be used for any metric type.
    All configuration comes from the database.
    
    This replaces the need for individual metric classes like RelevanceMetric,
    EmailProfessionalismMetric, etc. Just use this class and configure it
    from the database.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        evaluation_instructions: str,
        scale_min: int = 0,
        scale_max: int = 10,
        custom_format: Optional[str] = None,
        additional_context: Optional[str] = None,
        metric_type: str = "standard"
    ):
        """
        Initialize a generic metric from database configuration.
        
        Args:
            name: Metric name
            description: Metric description
            evaluation_instructions: Instructions for evaluation
            scale_min: Minimum score
            scale_max: Maximum score
            custom_format: Custom response format (optional)
            additional_context: Additional context (optional)
            metric_type: Type of metric ("standard", "mcp", or "email")
        """
        super().__init__(
            name=name,
            description=description,
            evaluation_instructions=evaluation_instructions,
            scale_min=scale_min,
            scale_max=scale_max,
            custom_format=custom_format,
            additional_context=additional_context
        )
        self.metric_type = metric_type


# Alias for backwards compatibility and clarity
GeneralMetric = GenericMetric
EmailMetric = GenericMetric
MCPMetric = GenericMetric
