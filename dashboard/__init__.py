"""
Dashboard module for LLM benchmarking results visualization.

This module provides HTML dashboard generation for visualizing
benchmark results with interactive charts and detailed analysis.
"""

from .data_processor import DashboardDataProcessor
from .html_generator import HTMLDashboardGenerator
from metrics.responses import BenchmarkResult

__all__ = [
    'DashboardDataProcessor',
    'HTMLDashboardGenerator',
    'generate_html_dashboard'
]


def generate_html_dashboard(benchmark_result: BenchmarkResult, output_path: str = "results/dashboard.html") -> str:
    """
    Convenience function to generate an HTML dashboard from benchmark results.
    
    Args:
        benchmark_result: The benchmark result to visualize
        output_path: Path where to save the HTML dashboard
        
    Returns:
        Path to the generated HTML file
    """
    # Process the data
    processor = DashboardDataProcessor(benchmark_result)
    
    # Generate the HTML dashboard
    generator = HTMLDashboardGenerator(processor)
    return generator.generate_dashboard(output_path) 