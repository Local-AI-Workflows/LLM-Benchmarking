from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np
from metrics.responses import EvaluatorResponse, BenchmarkResult
from datetime import datetime
import os
import seaborn as sns
from scipy.stats import pearsonr
import pandas as pd


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
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{height:.1f}',
                        ha='center', va='bottom', fontsize=8)

        # Add value labels for overall scores
        for bar in overall_bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=9, weight='bold')

        # Customize plot
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel("Metrics", fontsize=12)
        ax.set_ylabel("Average Score", fontsize=12)
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
        # Get metrics and determine actual number of evaluators from the data
        metrics = benchmark_result.metadata["metrics"]
        prompts = [eval.prompt for eval in benchmark_result.prompt_evaluations]

        # Determine actual number of evaluators from the first evaluation
        if benchmark_result.prompt_evaluations and benchmark_result.prompt_evaluations[0].evaluations:
            first_eval = benchmark_result.prompt_evaluations[0].evaluations[0]
            num_evaluators = len(first_eval.individual_responses)
            # Create model names based on actual evaluators
            model_names = [f"Evaluator {i + 1}" for i in range(num_evaluators)]
        else:
            # Fallback if no evaluations exist
            model_names = ["No Evaluators"]
            num_evaluators = 1

        # Calculate number of rows and columns for subplots
        n_metrics = len(metrics)
        n_cols = min(2, n_metrics)  # Maximum 2 columns
        n_rows = (n_metrics + 1) // 2  # Ceiling division

        # Create figure with subplots
        fig = plt.figure(figsize=(15, 5 * n_rows))

        # Create a heatmap for each metric
        for i, metric in enumerate(metrics):
            # Create a matrix of scores for this metric
            scores_matrix = np.zeros((len(prompts), num_evaluators))

            for j, prompt_eval in enumerate(benchmark_result.prompt_evaluations):
                for eval_result in prompt_eval.evaluations:
                    if eval_result.metric_name == metric:
                        for k, individual in enumerate(eval_result.individual_responses):
                            if k < num_evaluators:  # Safety check
                                scores_matrix[j, k] = individual.score

            # Create subplot
            ax = plt.subplot(n_rows, n_cols, i + 1)

            # Create heatmap
            sns.heatmap(scores_matrix,
                        annot=True,  # Show scores in cells
                        fmt='.1f',  # Format scores to 1 decimal place
                        cmap='RdYlGn',  # Red-Yellow-Green colormap
                        vmin=0, vmax=10,  # Score range
                        xticklabels=model_names,
                        yticklabels=[f"Q{i + 1}" for i in range(len(prompts))],
                        ax=ax)

            # Customize subplot
            ax.set_title(f"Scores by Question and Evaluator\n{metric}", fontweight='bold')
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

    def plot_radar_chart(self, benchmark_result: BenchmarkResult) -> plt.Figure:
        """
        Create a radar chart showing model performance across all metrics.

        Args:
            benchmark_result: The benchmark results to visualize

        Returns:
            matplotlib Figure object
        """
        # Get average scores by metric
        avg_scores = benchmark_result.get_average_scores_by_metric()
        metrics = list(avg_scores.keys())
        scores = list(avg_scores.values())

        # Number of metrics
        N = len(metrics)

        # Calculate angles for each metric
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Complete the circle

        # Add the first score to the end to complete the circle
        scores += scores[:1]

        # Create figure and polar subplot
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

        # Plot the scores
        ax.plot(angles, scores, 'o-', linewidth=2, label='Average Score', color='blue')
        ax.fill(angles, scores, alpha=0.25, color='blue')

        # Add metric labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics)

        # Set y-axis limits and labels
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(['2', '4', '6', '8', '10'])
        ax.grid(True)

        # Add title
        ax.set_title('Model Performance Across All Metrics', size=16, fontweight='bold', pad=20)

        # Add score values on the chart
        for angle, score in zip(angles[:-1], scores[:-1]):
            ax.text(angle, score + 0.3, f'{score:.1f}',
                    horizontalalignment='center', fontweight='bold', fontsize=10)

        return fig

    def plot_metric_correlation_matrix(self, benchmark_result: BenchmarkResult) -> plt.Figure:
        """
        Create a correlation matrix showing how different metrics correlate with each other.

        Args:
            benchmark_result: The benchmark results to visualize

        Returns:
            matplotlib Figure object
        """
        # Get all scores for each metric
        metrics = benchmark_result.metadata["metrics"]
        metric_scores = {}

        for metric in metrics:
            scores = []
            for evaluation in benchmark_result.prompt_evaluations:
                for eval_result in evaluation.evaluations:
                    if eval_result.metric_name == metric:
                        scores.append(eval_result.score)
            metric_scores[metric] = scores

        # Create correlation matrix
        correlation_matrix = np.zeros((len(metrics), len(metrics)))
        for i, metric1 in enumerate(metrics):
            for j, metric2 in enumerate(metrics):
                if i == j:
                    correlation_matrix[i, j] = 1.0
                else:
                    scores1 = metric_scores[metric1]
                    scores2 = metric_scores[metric2]
                    if len(scores1) == len(scores2) and len(scores1) > 1:
                        corr, _ = pearsonr(scores1, scores2)
                        correlation_matrix[i, j] = corr
                    else:
                        correlation_matrix[i, j] = 0.0

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))

        # Create heatmap
        sns.heatmap(correlation_matrix,
                    annot=True,
                    fmt='.2f',
                    cmap='coolwarm',
                    center=0,
                    vmin=-1, vmax=1,
                    xticklabels=metrics,
                    yticklabels=metrics,
                    ax=ax)

        ax.set_title('Metric Correlation Matrix', fontsize=14, fontweight='bold')
        plt.tight_layout()

        return fig

    def plot_question_difficulty_analysis(self, benchmark_result: BenchmarkResult) -> plt.Figure:
        """
        Create a plot showing question difficulty based on average scores.

        Args:
            benchmark_result: The benchmark results to visualize

        Returns:
            matplotlib Figure object
        """
        # Calculate average score for each question
        question_scores = []
        question_labels = []

        for i, evaluation in enumerate(benchmark_result.prompt_evaluations):
            scores = []
            for eval_result in evaluation.evaluations:
                scores.append(eval_result.score)

            avg_score = np.mean(scores) if scores else 0
            question_scores.append(avg_score)
            question_labels.append(f"Q{i + 1}")

        # Sort by difficulty (lowest scores = most difficult)
        sorted_data = sorted(zip(question_scores, question_labels))
        sorted_scores, sorted_labels = zip(*sorted_data)

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))

        # Create bar plot with color gradient
        colors = plt.cm.RdYlGn(np.array(sorted_scores) / 10.0)  # Normalize to 0-1 for colormap
        bars = ax.bar(range(len(sorted_scores)), sorted_scores, color=colors)

        # Add value labels on bars
        for bar, score in zip(bars, sorted_scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                    f'{score:.1f}',
                    ha='center', va='bottom', fontweight='bold')

        # Customize plot
        ax.set_title('Question Difficulty Analysis\n(Lower scores = More difficult)',
                     fontsize=14, fontweight='bold')
        ax.set_xlabel('Questions (sorted by difficulty)', fontsize=12)
        ax.set_ylabel('Average Score Across All Metrics', fontsize=12)
        ax.set_xticks(range(len(sorted_labels)))
        ax.set_xticklabels(sorted_labels)
        ax.set_ylim(0, 10)
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)

        plt.tight_layout()
        return fig

    def plot_evaluator_agreement(self, benchmark_result: BenchmarkResult) -> plt.Figure:
        """
        Create a plot showing how much evaluators agree with each other.

        Args:
            benchmark_result: The benchmark results to visualize

        Returns:
            matplotlib Figure object
        """
        # Calculate standard deviation of scores for each question and metric
        agreement_data = []

        for evaluation in benchmark_result.prompt_evaluations:
            for eval_result in evaluation.evaluations:
                individual_scores = [resp.score for resp in eval_result.individual_responses]
                if len(individual_scores) > 1:
                    std_dev = np.std(individual_scores)
                    agreement_data.append({
                        'metric': eval_result.metric_name,
                        'std_dev': std_dev,
                        'avg_score': np.mean(individual_scores)
                    })

        if not agreement_data:
            # Create empty plot if no multi-evaluator data
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No multi-evaluator data available\nfor agreement analysis',
                    ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title('Evaluator Agreement Analysis', fontsize=14, fontweight='bold')
            return fig

        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(agreement_data)

        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Plot 1: Agreement by metric (lower std_dev = higher agreement)
        metric_agreement = df.groupby('metric')['std_dev'].mean().sort_values()
        bars1 = ax1.bar(range(len(metric_agreement)), metric_agreement.values,
                        color=plt.cm.RdYlGn_r(metric_agreement.values / metric_agreement.max()))

        ax1.set_title('Evaluator Agreement by Metric\n(Lower = More Agreement)', fontweight='bold')
        ax1.set_xlabel('Metrics')
        ax1.set_ylabel('Average Standard Deviation')
        ax1.set_xticks(range(len(metric_agreement)))
        ax1.set_xticklabels(metric_agreement.index, rotation=45, ha='right')
        ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

        # Add value labels
        for bar, value in zip(bars1, metric_agreement.values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height + 0.01,
                     f'{value:.2f}',
                     ha='center', va='bottom', fontweight='bold')

        # Plot 2: Scatter plot of agreement vs average score
        ax2.scatter(df['avg_score'], df['std_dev'], alpha=0.6, s=50)
        ax2.set_xlabel('Average Score')
        ax2.set_ylabel('Standard Deviation (Disagreement)')
        ax2.set_title('Score vs Agreement Relationship', fontweight='bold')
        ax2.grid(True, linestyle='--', alpha=0.7)

        # Add trend line
        z = np.polyfit(df['avg_score'], df['std_dev'], 1)
        p = np.poly1d(z)
        ax2.plot(df['avg_score'], p(df['avg_score']), "r--", alpha=0.8, linewidth=2)

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