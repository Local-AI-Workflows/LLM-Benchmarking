from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np
from metrics.responses import EvaluatorResponse, BenchmarkResult


class EvaluationVisualizer:
    """Visualizes evaluation results using matplotlib."""

    def __init__(self, figsize=(12, 6)):
        self.figsize = figsize

    def plot_benchmark_results(self, benchmark_result: BenchmarkResult, title: str = "Benchmark Results"):
        """
        Plot benchmark results across all prompts and metrics.
        
        Args:
            benchmark_result: BenchmarkResult containing all evaluation data
            title: Title for the plot
        """
        plt.figure(figsize=self.figsize)
        
        # Get average scores by metric
        avg_scores = benchmark_result.get_average_scores_by_metric()
        model_scores = benchmark_result.get_model_scores_by_metric()
        
        # Prepare data for plotting
        metric_names = list(avg_scores.keys())
        model_names = list(model_scores.keys())
        x = np.arange(len(metric_names))
        width = 0.8 / len(model_names)
        
        # Plot bars for each model
        for i, model_name in enumerate(model_names):
            scores = []
            for metric in metric_names:
                if metric in model_scores[model_name]:
                    # Calculate average score for this model and metric
                    scores.append(sum(model_scores[model_name][metric]) / len(model_scores[model_name][metric]))
                else:
                    scores.append(0)
            
            # Calculate offset for bar position
            offset = (i - len(model_names) / 2 + 0.5) * width
            plt.bar(x + offset, scores, width, label=model_name)
        
        # Plot overall average scores
        plt.plot(x, [avg_scores[metric] for metric in metric_names], 
                'r--', label='Overall Average', linewidth=2)
        
        # Customize the plot
        plt.xlabel('Metrics')
        plt.ylabel('Average Score')
        plt.title(title)
        plt.xticks(x, metric_names, rotation=45, ha='right')
        plt.legend()
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Add metadata to the plot
        metadata_text = f"Number of prompts: {benchmark_result.metadata['num_prompts']}"
        plt.figtext(0.02, 0.02, metadata_text, fontsize=8)
        
        plt.tight_layout()
        return plt.gcf()

    def plot_metric_details(self, benchmark_result: BenchmarkResult, metric_name: str, title: str = None):
        """
        Plot detailed comparison for a specific metric across all prompts.
        
        Args:
            benchmark_result: BenchmarkResult containing all evaluation data
            metric_name: Name of the metric to plot
            title: Optional title for the plot
        """
        plt.figure(figsize=self.figsize)
        
        # Get scores for this metric
        model_scores = benchmark_result.get_model_scores_by_metric()
        
        # Prepare data
        model_names = []
        scores = []
        std_devs = []
        
        for model_name, metric_scores in model_scores.items():
            if metric_name in metric_scores:
                model_names.append(model_name)
                scores.append(np.mean(metric_scores[metric_name]))
                std_devs.append(np.std(metric_scores[metric_name]))
        
        # Create bar plot with error bars
        bars = plt.bar(model_names, scores, yerr=std_devs, capsize=5)
        
        # Add score labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom')
        
        # Customize the plot
        plt.title(title or f"{metric_name} Comparison Across {benchmark_result.metadata['num_prompts']} Prompts")
        plt.xlabel('Models')
        plt.ylabel('Average Score')
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Rotate x-axis labels if needed
        if len(model_names) > 3:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        return plt.gcf()

    def save_plot(self, figure, filename: str):
        """Save the plot to a file."""
        figure.savefig(filename, bbox_inches='tight', dpi=300)
        plt.close(figure) 