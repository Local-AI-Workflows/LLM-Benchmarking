"""Utility functions for loading metrics from the database."""

import importlib
import logging
from typing import List, Optional
from database.connection import Database
from database.metric_repository import MetricRepository
from database.models import MetricDocument
from .metric_base import BaseMetric, StandardMetric

logger = logging.getLogger(__name__)

# Re-export load_metric_from_db for convenience
__all__ = ['load_metric_from_db', 'load_metrics_from_db', 'list_available_metrics_from_db', 'get_generic_metric_class']


def get_generic_metric_class():
    """
    Get the generic metric class that can be used for any metric.
    
    Returns:
        GenericMetric class
    """
    from .generic_metrics import GenericMetric
    return GenericMetric


def load_metric_from_db(metric_doc: MetricDocument) -> BaseMetric:
    """
    Load a metric instance from database document, using stored configuration.
    
    Uses the generic GenericMetric class - no need for individual metric classes.
    All configuration comes from the database.
    
    Args:
        metric_doc: MetricDocument from database
        
    Returns:
        BaseMetric instance configured with database settings
        
    Raises:
        ValueError: If metric cannot be loaded
    """
    try:
        # Use the generic metric class - no need to import specific classes
        GenericMetric = get_generic_metric_class()
        
        # Create metric with configuration from database
        return GenericMetric(
            name=metric_doc.name,
            description=metric_doc.description,
            evaluation_instructions=metric_doc.evaluation_instructions or "",
            scale_min=metric_doc.scale_min,
            scale_max=metric_doc.scale_max,
            custom_format=metric_doc.custom_format,
            additional_context=metric_doc.additional_context,
            metric_type=metric_doc.type
        )
    except Exception as e:
        raise ValueError(f"Failed to load metric {metric_doc.name}: {e}")


async def load_metrics_from_db(
    metric_names: Optional[List[str]] = None,
    metric_type: Optional[str] = None,
    enabled_only: bool = True
) -> List[BaseMetric]:
    """
    Load metrics from the database.
    
    Args:
        metric_names: Optional list of metric names to load. If None, loads all matching metrics.
        metric_type: Optional metric type filter ("standard" or "mcp")
        enabled_only: Only load enabled metrics (default: True)
        
    Returns:
        List of BaseMetric instances
        
    Raises:
        ValueError: If database is not connected or metrics not found
    """
    # Ensure database is connected
    if not Database.is_connected():
        await Database.connect()
    
    repo = MetricRepository()
    metrics = []
    
    if metric_names:
        # Load specific metrics by name
        for metric_name in metric_names:
            metric_doc = await repo.get_by_name(metric_name)
            if not metric_doc:
                raise ValueError(f"Metric '{metric_name}' not found in database")
            if not metric_doc.enabled and enabled_only:
                logger.warning(f"Metric '{metric_name}' is disabled, skipping")
                continue
            if metric_type and metric_doc.type != metric_type:
                logger.warning(f"Metric '{metric_name}' type mismatch (expected {metric_type}, got {metric_doc.type}), skipping")
                continue
            
            try:
                metric = load_metric_from_db(metric_doc)
                metrics.append(metric)
            except Exception as e:
                logger.error(f"Failed to load metric '{metric_name}': {e}")
                raise
    else:
        # Load all metrics matching criteria
        metric_docs = await repo.get_all(
            metric_type=metric_type,
            enabled_only=enabled_only
        )
        
        for metric_doc in metric_docs:
            try:
                metric = load_metric_from_db(metric_doc)
                metrics.append(metric)
            except Exception as e:
                logger.error(f"Failed to load metric '{metric_doc.name}': {e}")
                # Continue loading other metrics even if one fails
                continue
    
    if not metrics:
        error_msg = "No metrics found"
        if metric_names:
            error_msg += f" for names: {', '.join(metric_names)}"
        if metric_type:
            error_msg += f" of type: {metric_type}"
        if enabled_only:
            error_msg += " (enabled only)"
        raise ValueError(error_msg)
    
    return metrics


async def list_available_metrics_from_db(
    metric_type: Optional[str] = None,
    enabled_only: bool = True
) -> List[str]:
    """
    List available metric names from the database.
    
    Args:
        metric_type: Optional metric type filter ("standard" or "mcp")
        enabled_only: Only list enabled metrics (default: True)
        
    Returns:
        List of metric names
    """
    # Ensure database is connected
    if not Database.is_connected():
        await Database.connect()
    
    repo = MetricRepository()
    metric_docs = await repo.get_all(
        metric_type=metric_type,
        enabled_only=enabled_only
    )
    
    return [doc.name for doc in metric_docs]
