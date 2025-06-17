from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np
from metrics.responses import EvaluatorResponse, BenchmarkResult
from datetime import datetime
import os
import seaborn as sns


class EvaluationVisualizer:
    """Visualizes evaluation results using matplotlib."""

    def __init__(self, results_dir: str = "results"):
        """
        Initialize the visualizer.
        
        Args:
            results_dir: Directory to save visualization results
        """
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def plot_benchmark_results(self, benchmark_result: BenchmarkResult, title: str) -> plt.Figure:
        """
        Create a bar plot of average scores by metric, showing both overall and individual model scores.
        
        Args:
            benchmark_result: The benchmark results to visualize
            title: Title for the plot
            
        Returns:
            matplotlib Figure object
        """
        # Get average scores by metric
        avg_scores = benchmark_result.get_average_scores_by_metric()
        
        # Prepare data for plotting
        metric_names = list(avg_scores.keys())
        overall_scores = list(avg_scores.values())
        
        # Get individual model scores for each metric
        model_scores = {}
        for metric in metric_names:
            scores = benchmark_result.get_model_scores_by_metric(metric)
            model_scores[metric] = scores
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Set up bar positions
        x = np.arange(len(metric_names))
        width = 0.8 / (len(model_scores[metric_names[0]]) + 1)  # +1 for overall score
        
        # Plot overall scores
        overall_bars = ax.bar(x, overall_scores, width, label='Overall Average', color='black', alpha=0.7)
        
        # Plot individual model scores
        colors = plt.cm.Set3(np.linspace(0, 1, len(model_scores[metric_names[0]])))
        for i, (model_name, scores) in enumerate(model_scores[metric_names[0]].items()):
            model_avg_scores = [np.mean(model_scores[metric][model_name]) for metric in metric_names]
            offset = (i + 1) * width
            model_bars = ax.bar(x + offset, model_avg_scores, width, label=model_name, color=colors[i])
            
            # Add value labels for individual model scores
            for bar in model_bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}',
                       ha='center', va='bottom', fontsize=8)
        
        # Add value labels for overall scores
        for bar in overall_bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=9, weight='bold')
        
        # Customize plot
        ax.set_title(title)
        ax.set_xlabel("Metrics")
        ax.set_ylabel("Average Score")
        ax.set_ylim(0, 10)  # Assuming scores are on a 0-10 scale
        ax.set_xticks(x + width * (len(model_scores[metric_names[0]]) / 2))
        ax.set_xticklabels(metric_names, rotation=45, ha='right')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Add grid for better readability
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        return fig

    def plot_metric_details(self, benchmark_result: BenchmarkResult, metric_name: str) -> plt.Figure:
        """
        Create a detailed plot for a specific metric showing score distribution for each model.
        
        Args:
            benchmark_result: The benchmark results to visualize
            metric_name: Name of the metric to plot
            
        Returns:
            matplotlib Figure object
        """
        # Get scores for the metric by model
        model_scores = benchmark_result.get_model_scores_by_metric(metric_name)
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot distribution for each model
        for model_name, scores in model_scores.items():
            sns.kdeplot(scores, label=model_name, ax=ax)
        
        # Add mean lines for each model
        for model_name, scores in model_scores.items():
            mean_score = np.mean(scores)
            ax.axvline(mean_score, linestyle='--', alpha=0.5,
                      label=f'{model_name} Mean: {mean_score:.2f}')
        
        # Customize plot
        ax.set_title(f"Score Distribution for {metric_name}")
        ax.set_xlabel("Score")
        ax.set_ylabel("Density")
        ax.set_xlim(0, 10)  # Assuming scores are on a 0-10 scale
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Add grid for better readability
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Adjust layout
        plt.tight_layout()
        
        return fig

    def plot_per_question_scores(self, benchmark_result: BenchmarkResult) -> plt.Figure:
        """
        Create heatmaps showing scores for each question by each evaluator model, separated by metric.
        
        Args:
            benchmark_result: The benchmark results to visualize
            
        Returns:
            matplotlib Figure object
        """
        # Get metrics and model names
        metrics = benchmark_result.metadata["metrics"]
        model_names = benchmark_result.metadata["evaluator_models"]
        prompts = [eval.prompt for eval in benchmark_result.prompt_evaluations]
        
        # Calculate number of rows and columns for subplots
        n_metrics = len(metrics)
        n_cols = min(2, n_metrics)  # Maximum 2 columns
        n_rows = (n_metrics + 1) // 2  # Ceiling division
        
        # Create figure with subplots
        fig = plt.figure(figsize=(15, 5 * n_rows))
        
        # Create a heatmap for each metric
        for i, metric in enumerate(metrics):
            # Create a matrix of scores for this metric
            scores_matrix = np.zeros((len(prompts), len(model_names)))
            
            for j, prompt_eval in enumerate(benchmark_result.prompt_evaluations):
                for eval_result in prompt_eval.evaluations:
                    if eval_result.metric_name == metric:
                        for k, individual in enumerate(eval_result.individual_responses):
                            scores_matrix[j, k] = individual.score
            
            # Create subplot
            ax = plt.subplot(n_rows, n_cols, i + 1)
            
            # Create heatmap
            sns.heatmap(scores_matrix, 
                       annot=True,  # Show scores in cells
                       fmt='.1f',   # Format scores to 1 decimal place
                       cmap='RdYlGn',  # Red-Yellow-Green colormap
                       vmin=0, vmax=10,  # Score range
                       xticklabels=model_names,
                       yticklabels=[f"Q{i+1}" for i in range(len(prompts))],
                       ax=ax)
            
            # Customize subplot
            ax.set_title(f"Scores by Question and Evaluator\n{metric}")
            ax.set_xlabel("Evaluator Model")
            ax.set_ylabel("Question")
            
            # Add colorbar label
            cbar = ax.collections[0].colorbar
            cbar.set_label("Score")
        
        # Adjust layout
        plt.tight_layout()
        
        return fig

    def plot_model_summary(self, benchmark_result: BenchmarkResult) -> plt.Figure:
        """
        Create a summary plot showing overall performance of each model across all metrics.
        
        Args:
            benchmark_result: The benchmark results to visualize
            
        Returns:
            matplotlib Figure object
        """
        # Get model scores by metric
        model_scores = {}
        for metric in benchmark_result.metadata["metrics"]:
            scores = benchmark_result.get_model_scores_by_metric(metric)
            for model_name, model_scores_list in scores.items():
                if model_name not in model_scores:
                    model_scores[model_name] = []
                model_scores[model_name].extend(model_scores_list)
        
        # Calculate statistics for each model
        model_stats = {
            model: {
                'mean': np.mean(scores),
                'std': np.std(scores),
                'min': np.min(scores),
                'max': np.max(scores)
            }
            for model, scores in model_scores.items()
        }
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot box plots for each model
        box_data = [model_scores[model] for model in model_scores.keys()]
        box = ax.boxplot(box_data, 
                        labels=list(model_scores.keys()),
                        patch_artist=True)
        
        # Customize box plot colors
        colors = plt.cm.Set3(np.linspace(0, 1, len(model_scores)))
        for patch, color in zip(box['boxes'], colors):
            patch.set_facecolor(color)
        
        # Add mean points
        means = [stats['mean'] for stats in model_stats.values()]
        ax.plot(range(1, len(means) + 1), means, 'r*', markersize=10, label='Mean')
        
        # Customize plot
        ax.set_title("Model Performance Summary")
        ax.set_xlabel("Model")
        ax.set_ylabel("Score")
        ax.set_ylim(0, 10)  # Assuming scores are on a 0-10 scale
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        ax.legend()
        
        # Add statistics as text
        stats_text = "\n".join([
            f"{model}:\n"
            f"Mean: {stats['mean']:.2f}\n"
            f"Std: {stats['std']:.2f}\n"
            f"Range: [{stats['min']:.2f}, {stats['max']:.2f}]"
            for model, stats in model_stats.items()
        ])
        ax.text(1.02, 0.5, stats_text,
                transform=ax.transAxes,
                verticalalignment='center',
                bbox=dict(facecolor='white', alpha=0.8))
        
        # Adjust layout
        plt.tight_layout()
        
        return fig

    def save_plot(self, figure: plt.Figure, filename: str):
        """
        Save a plot to a file.
        
        Args:
            figure: The matplotlib Figure to save
            filename: Name of the file to save to
        """
        filepath = os.path.join(self.results_dir, filename)
        figure.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close(figure) 