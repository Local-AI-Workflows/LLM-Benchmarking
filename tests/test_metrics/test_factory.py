"""
Unit tests for MetricFactory and metric creation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from metrics import MetricFactory, BaseMetric, get_all_metrics, get_metric_by_name
from metrics.responses import EvaluatorResponse


class TestMetricFactory:
    """Test cases for MetricFactory."""
    
    @pytest.mark.unit
    def test_list_available_metrics(self):
        """Test getting list of available metrics."""
        metrics = MetricFactory.list_available_metrics()
        
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        
        # Check that some expected metrics are present
        assert "relevance" in metrics
        assert "hallucinations" in metrics
        assert "fairness" in metrics
        assert "toxicity" in metrics
    
    @pytest.mark.unit
    def test_create_metric_by_name(self):
        """Test creating metrics by name."""
        # Test creating a known metric
        relevance_metric = MetricFactory.create_metric("relevance")
        
        assert isinstance(relevance_metric, BaseMetric)
        
        # Test creating another metric
        toxicity_metric = MetricFactory.create_metric("toxicity")
        
        assert isinstance(toxicity_metric, BaseMetric)
    
    @pytest.mark.unit
    def test_create_metric_invalid_name(self):
        """Test creating metric with invalid name."""
        with pytest.raises(ValueError) as exc_info:
            MetricFactory.create_metric("nonexistent_metric")
        
        assert "Unknown metric" in str(exc_info.value)
        assert "nonexistent_metric" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_create_metrics_by_names(self):
        """Test creating multiple metrics at once."""
        metric_names = ["relevance", "toxicity", "fairness"]
        metrics = MetricFactory.create_metrics_by_names(metric_names)
        
        assert len(metrics) == 3
        assert all(isinstance(m, BaseMetric) for m in metrics)
    
    @pytest.mark.unit
    def test_create_metrics_by_names_with_invalid(self):
        """Test creating metrics with some invalid names."""
        metric_names = ["relevance", "invalid_metric", "toxicity"]
        
        with pytest.raises(ValueError) as exc_info:
            MetricFactory.create_metrics_by_names(metric_names)
        
        assert "Unknown metric" in str(exc_info.value)
        assert "invalid_metric" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_create_all_metrics(self):
        """Test creating all available metrics."""
        metrics = MetricFactory.create_all_metrics()
        
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert all(isinstance(m, BaseMetric) for m in metrics)
        
        # Should have at least the expected metrics
        available_count = len(MetricFactory.list_available_metrics())
        assert len(metrics) == available_count
    
    @pytest.mark.unit
    def test_factory_methods_are_static(self):
        """Test that factory methods can be called without instantiation."""
        # Should be able to call without creating an instance
        names = MetricFactory.list_available_metrics()
        assert isinstance(names, list)
        
        metric = MetricFactory.create_metric("relevance")
        assert isinstance(metric, BaseMetric)
        
        all_metrics = MetricFactory.create_all_metrics()
        assert isinstance(all_metrics, list)


class TestMetricRegistry:
    """Test cases for the metric registry functions."""
    
    @pytest.mark.unit
    def test_get_all_metrics(self):
        """Test getting all metrics from registry."""
        metrics = get_all_metrics()
        
        assert isinstance(metrics, dict)
        assert len(metrics) > 0
        
        # Check that some expected metrics are present
        assert "relevance" in metrics
        assert "toxicity" in metrics
        assert "fairness" in metrics
        
        # All values should be classes
        for name, metric_class in metrics.items():
            assert isinstance(name, str)
            assert isinstance(metric_class, type)
    
    @pytest.mark.unit
    def test_get_metric_by_name(self):
        """Test getting metric class by name."""
        # Test getting a known metric
        relevance_class = get_metric_by_name("relevance")
        assert isinstance(relevance_class, type)
        
        # Should be able to instantiate it
        instance = relevance_class()
        assert isinstance(instance, BaseMetric)
    
    @pytest.mark.unit
    def test_get_metric_by_name_invalid(self):
        """Test getting metric with invalid name."""
        with pytest.raises(ValueError) as exc_info:
            get_metric_by_name("nonexistent_metric")
        
        assert "Unknown metric" in str(exc_info.value)
        assert "nonexistent_metric" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_registry_consistency(self):
        """Test that registry is consistent across different access methods."""
        # Get metrics through different methods
        all_metrics = get_all_metrics()
        available_names = MetricFactory.list_available_metrics()
        
        # Names should match
        assert set(all_metrics.keys()) == set(available_names)
        
        # All metrics should be creatable
        for name in available_names:
            metric_class = get_metric_by_name(name)
            assert metric_class in all_metrics.values()
            
            # Should be able to create instance
            instance = MetricFactory.create_metric(name)
            assert isinstance(instance, BaseMetric)
    
    @pytest.mark.unit
    def test_metric_classes_are_valid(self):
        """Test that all metric classes are valid and instantiable."""
        metrics = get_all_metrics()
        
        for name, metric_class in metrics.items():
            # Should be a class
            assert isinstance(metric_class, type)
            
            # Should be a subclass of BaseMetric
            assert issubclass(metric_class, BaseMetric)
            
            # Should be instantiable
            instance = metric_class()
            assert isinstance(instance, BaseMetric)
    
    @pytest.mark.unit
    def test_registry_immutability(self):
        """Test that the metric registry cannot be easily modified."""
        original_metrics = get_all_metrics()
        original_count = len(original_metrics)
        
        # Try to modify the returned dict (should not affect internal registry)
        returned_metrics = get_all_metrics()
        returned_metrics.clear()
        
        # Registry should still be intact
        new_metrics = get_all_metrics()
        assert len(new_metrics) == original_count
    
    @pytest.mark.unit
    def test_metric_uniqueness(self):
        """Test that all registered metrics have unique names."""
        metrics = get_all_metrics()
        names = list(metrics.keys())
        
        # Should have no duplicates
        assert len(names) == len(set(names))
    
    @pytest.mark.unit
    def test_error_messages_are_helpful(self):
        """Test that error messages provide helpful information."""
        try:
            get_metric_by_name("nonexistent_metric")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_msg = str(e)
            
            # Should mention the invalid metric name
            assert "nonexistent_metric" in error_msg
            
            # Should provide available options
            assert "Available:" in error_msg


class TestMetricFactoryPerformance:
    """Test cases for MetricFactory performance."""
    
    @pytest.mark.unit
    def test_factory_performance(self):
        """Test that factory operations are reasonably fast."""
        import time
        
        # Getting available metrics should be fast
        start = time.time()
        for _ in range(100):
            MetricFactory.list_available_metrics()
        duration = time.time() - start
        assert duration < 1.0  # Should complete in under 1 second
        
        # Creating metrics should be fast
        start = time.time()
        for _ in range(50):
            MetricFactory.create_metric("relevance")
        duration = time.time() - start
        assert duration < 1.0  # Should complete in under 1 second
    
    @pytest.mark.unit
    def test_create_all_metrics_performance(self):
        """Test that creating all metrics is reasonably fast."""
        import time
        
        start = time.time()
        for _ in range(10):
            MetricFactory.create_all_metrics()
        duration = time.time() - start
        assert duration < 2.0  # Should complete in under 2 seconds


class TestMetricFactoryEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.unit
    def test_create_metrics_empty_list(self):
        """Test creating metrics with empty list."""
        metrics = MetricFactory.create_metrics_by_names([])
        assert metrics == []
    
    @pytest.mark.unit
    def test_create_metrics_duplicates(self):
        """Test creating metrics with duplicate names."""
        metric_names = ["relevance", "toxicity", "relevance"]
        metrics = MetricFactory.create_metrics_by_names(metric_names)
        
        # Should still create 3 metrics (duplicates allowed)
        assert len(metrics) == 3
        
        # Should have two relevance metrics
        relevance_count = sum(1 for m in metrics if type(m).__name__ == "RelevanceMetric")
        assert relevance_count == 2
    
    @pytest.mark.unit
    def test_metric_creation_basic(self):
        """Test basic metric creation functionality."""
        # Test that normal creation works
        metric = MetricFactory.create_metric("relevance")
        assert isinstance(metric, BaseMetric)
        
        # Test that each created metric is a separate instance
        metric1 = MetricFactory.create_metric("relevance")
        metric2 = MetricFactory.create_metric("relevance")
        assert metric1 is not metric2
    
    @pytest.mark.unit
    def test_all_metrics_have_required_methods(self):
        """Test that all metrics have the required methods."""
        metrics = MetricFactory.create_all_metrics()
        
        for metric in metrics:
            # Should have evaluate method
            assert hasattr(metric, 'evaluate')
            assert callable(metric.evaluate)
            
            # Should have name attribute
            assert hasattr(metric, 'name')
            assert isinstance(metric.name, str)
            assert len(metric.name) > 0 