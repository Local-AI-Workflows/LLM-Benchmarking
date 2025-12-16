import asyncio
import argparse
import os
from datetime import datetime
from models.ollama_model import OllamaModel, OllamaConfig
from metrics import EvaluatorFactory
from metrics.database_loader import load_metrics_from_db, list_available_metrics_from_db
from metrics.responses import BenchmarkResult
from benchmark.runner import BenchmarkRunner
from visualizations.evaluation_visualizer import EvaluationVisualizer
from dashboard import generate_html_dashboard
from dataset import DatasetLoader, Dataset, Question
from database.connection import Database


def create_default_dataset() -> Dataset:
    """Create the default test dataset."""
    prompts = [
        "What is the capital of France?",
        "Explain the concept of quantum computing in simple terms.",
        "Write a short poem about artificial intelligence.",
        "If a train travels at 60 mph for 2.5 hours, how far does it go?",
        "Write a Python function to calculate the Fibonacci sequence."
    ]
    
    # Convert to a proper dataset with some metadata
    questions = [
        Question.from_string(prompts[0]),
        Question.from_string(prompts[1]),
        Question.from_string(prompts[2]),
        Question.from_string(prompts[3]),
        Question.from_string(prompts[4])
    ]
    
    return Dataset(
        questions=questions,
        name="Default Benchmark Dataset",
        description="Standard test questions for LLM evaluation"
    )


async def run_new_benchmark(dataset: Dataset, selected_metrics: list = None):
    """Run a new benchmark and return the results."""
    # Ensure database is connected
    if not Database.is_connected():
        await Database.connect()
    
    # Initialize the model to evaluate
    test_model = OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
    
    # Initialize evaluator models
    evaluator_models = [
        OllamaModel(config=OllamaConfig(model_name="deepseek-r1:1.5b")),
        OllamaModel(config=OllamaConfig(model_name="gemma3:1b")),
        OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
    ]
    evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
    
    # Initialize metrics from database
    if selected_metrics:
        print(f"Using selected metrics: {', '.join(selected_metrics)}")
        metrics = await load_metrics_from_db(metric_names=selected_metrics)
    else:
        print("Using all available metrics from database")
        metrics = await load_metrics_from_db()
    
    # Create benchmark runner
    runner = BenchmarkRunner(evaluator, metrics)
    
    # Run benchmark with dataset
    print(f"\nRunning benchmark with dataset: {dataset.name}")
    print(f"Dataset description: {dataset.description}")
    print(f"Number of questions: {len(dataset)}")
    print(f"Number of metrics: {len(metrics)}")
    
    # Display dataset statistics
    stats = dataset.get_statistics()
    print(f"Languages: {list(stats['languages'].keys())}")
    
    benchmark_result = await runner.run_benchmark(test_model, dataset)
    
    return benchmark_result


def load_dataset(args) -> Dataset:
    """Load dataset from command line arguments."""
    if args.dataset_file:
        print(f"Loading dataset from file: {args.dataset_file}")
        
        try:
            if args.dataset_format:
                # Use specific loader based on format
                if args.dataset_format == 'json':
                    dataset = DatasetLoader.from_json_file(args.dataset_file)
                elif args.dataset_format == 'csv':
                    dataset = DatasetLoader.from_csv_file(
                        args.dataset_file,
                        text_column=args.text_column
                    )
                elif args.dataset_format == 'yaml':
                    dataset = DatasetLoader.from_yaml_file(args.dataset_file)
                elif args.dataset_format == 'txt':
                    dataset = DatasetLoader.from_text_file(args.dataset_file)
                else:
                    raise ValueError(f"Unsupported format: {args.dataset_format}")
            else:
                # Auto-detect format
                dataset = DatasetLoader.load_from_file(args.dataset_file)
            
            print(f"✓ Successfully loaded dataset: {dataset.name}")
            return dataset
            
        except Exception as e:
            print(f"Failed to load dataset: {e}")
            print("Using default dataset instead...")
            return create_default_dataset()
    
    elif args.dataset_sample:
        print("Using sample dataset for demonstration...")
        return DatasetLoader.create_sample_dataset()
    
    else:
        print("Using default dataset...")
        return create_default_dataset()


async def parse_metrics(args) -> list:
    """Parse and validate metric selection from command line arguments."""
    if not args.metrics:
        return None  # Use all metrics
    
    # Ensure database is connected
    if not Database.is_connected():
        await Database.connect()
    
    available_metrics = await list_available_metrics_from_db()
    selected_metrics = [m.strip() for m in args.metrics.split(',')]
    
    # Validate metric names
    invalid_metrics = [m for m in selected_metrics if m not in available_metrics]
    if invalid_metrics:
        print(f"Invalid metrics: {', '.join(invalid_metrics)}")
        print(f"Available metrics: {', '.join(available_metrics)}")
        raise ValueError(f"Invalid metrics specified: {', '.join(invalid_metrics)}")
    
    return selected_metrics


def generate_visualizations(benchmark_result: BenchmarkResult, results_dir: str = "results"):
    """Generate and save visualizations for the benchmark results."""
    print(f"\nGenerating visualizations in '{results_dir}' directory...")
    
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)
    
    visualizer = EvaluationVisualizer(results_dir=results_dir)
    
    # Use dataset name in titles if available
    dataset_name = benchmark_result.metadata.get("dataset_name", "Dataset")
    title_suffix = f"using {dataset_name}"
    
    # Plot overall results (bar chart)
    figure = visualizer.plot_benchmark_results(benchmark_result, f"Benchmark Results {title_suffix}")
    visualizer.save_plot(figure, "benchmark_results.png")
    
    # Plot per-question scores (heatmaps)
    figure = visualizer.plot_per_question_scores(benchmark_result)
    visualizer.save_plot(figure, "per_question_scores.png")
    
    # Plot radar chart showing overall performance
    figure = visualizer.plot_radar_chart(benchmark_result)
    visualizer.save_plot(figure, "performance_radar.png")
    
    # Plot metric correlation matrix
    figure = visualizer.plot_metric_correlation_matrix(benchmark_result)
    visualizer.save_plot(figure, "metric_correlations.png")
    
    # Plot question difficulty analysis
    figure = visualizer.plot_question_difficulty_analysis(benchmark_result)
    visualizer.save_plot(figure, "question_difficulty.png")
    
    # Plot evaluator agreement analysis
    figure = visualizer.plot_evaluator_agreement(benchmark_result)
    visualizer.save_plot(figure, "evaluator_agreement.png")
    
    # Generate interactive HTML dashboard
    print("Generating interactive HTML dashboard...")
    dashboard_path = os.path.join(results_dir, "dashboard.html")
    try:
        generated_path = generate_html_dashboard(benchmark_result, dashboard_path)
        print(f"✓ Interactive dashboard saved to: {generated_path}")
    except Exception as e:
        print(f"Failed to generate HTML dashboard: {e}")
        print("  Static visualizations are still available")


async def main():
    """Main function with command line argument support."""
    parser = argparse.ArgumentParser(description="LLM Benchmark Tool with Enhanced Metrics System")
    
    # JSON import/export options
    parser.add_argument(
        "--import-json", 
        type=str, 
        help="Import benchmark results from JSON file instead of running new benchmark"
    )
    parser.add_argument(
        "--export-json", 
        type=str, 
        help="Export benchmark results to JSON file (default: results/benchmark_results_<timestamp>.json)"
    )
    
    # Dataset options
    parser.add_argument(
        "--dataset-file",
        type=str,
        help="Path to dataset file (JSON, CSV, YAML, or TXT format)"
    )
    parser.add_argument(
        "--dataset-format",
        type=str,
        choices=['json', 'csv', 'yaml', 'txt'],
        help="Force specific dataset format (auto-detected if not specified)"
    )
    parser.add_argument(
        "--dataset-sample",
        action="store_true",
        help="Use built-in sample dataset for demonstration"
    )
    
    # CSV-specific options
    parser.add_argument(
        "--text-column",
        type=str,
        default="text",
        help="CSV column name containing question text (default: 'text')"
    )
    
    # Metric selection options
    parser.add_argument(
        "--metrics",
        type=str,
        help="Comma-separated list of metrics to use. Use --list-metrics to see available metrics."
    )
    parser.add_argument(
        "--list-metrics",
        action="store_true",
        help="List all available metrics and exit"
    )
    
    # General options
    parser.add_argument(
        "--results-dir", 
        type=str, 
        default="results", 
        help="Directory to save results and visualizations (default: results)"
    )
    parser.add_argument(
        "--skip-visualizations", 
        action="store_true", 
        help="Skip generating visualizations"
    )
    
    args = parser.parse_args()
    
    # Ensure database is connected
    if not Database.is_connected():
        await Database.connect()
    
    # Handle list metrics option
    if args.list_metrics:
        print("Available metrics from database:")
        try:
            available_metrics = await list_available_metrics_from_db()
            from database.metric_repository import MetricRepository
            repo = MetricRepository()
            for metric_name in available_metrics:
                metric_doc = await repo.get_by_name(metric_name)
                if metric_doc:
                    print(f"  {metric_name} ({metric_doc.type}): {metric_doc.description}")
        except Exception as e:
            print(f"Error loading metrics: {e}")
        finally:
            await Database.disconnect()
        return
    
    # Parse metric selection
    try:
        selected_metrics = await parse_metrics(args)
    except ValueError as e:
        print(str(e))
        await Database.disconnect()
        return
    
    # Import existing results or run new benchmark
    if args.import_json:
        print(f"\nImporting benchmark results from: {args.import_json}")
        try:
            benchmark_result = BenchmarkResult.load_from_json_file(args.import_json)
            print("✓ Successfully imported benchmark results from JSON")
            
            # Display basic information about imported results
            summary = benchmark_result.get_summary_statistics()
            print(f"  - Number of prompts: {summary['num_prompts']}")
            print(f"  - Metrics: {', '.join(summary['metrics'])}")
            print(f"  - Model: {summary['model_name']}")
            print(f"  - Overall average score: {summary['overall_average']}")
            
        except Exception as e:
            print(f"Failed to import JSON file: {e}")
            await Database.disconnect()
            return
    else:
        # Load dataset
        dataset = load_dataset(args)
        
        # Run new benchmark
        try:
            benchmark_result = await run_new_benchmark(dataset, selected_metrics)
            print("✓ Benchmark completed successfully")
        finally:
            await Database.disconnect()
    
    # Export results to JSON if requested or if running new benchmark
    export_path = args.export_json
    if not args.import_json or export_path:  # Always export for new benchmarks, or if explicitly requested
        if not export_path:
            # Generate default export path with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(args.results_dir, exist_ok=True)
            export_path = os.path.join(args.results_dir, f"benchmark_results_{timestamp}.json")
        
        print(f"\nExporting benchmark results to: {export_path}")
        try:
            benchmark_result.save_to_json_file(export_path)
            print("✓ Successfully exported benchmark results to JSON")
        except Exception as e:
            print(f"Failed to export to JSON file: {e}")
    
    # Generate visualizations unless skipped
    if not args.skip_visualizations:
        generate_visualizations(benchmark_result, args.results_dir)
        print(f"✓ Visualizations saved to '{args.results_dir}' directory")
    
    # Display enhanced summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    
    summary = benchmark_result.get_summary_statistics()
    print(f"Model: {summary['model_name']}")
    print(f"Dataset: {benchmark_result.metadata.get('dataset_name', 'Unknown')}")
    print(f"Number of prompts: {summary['num_prompts']}")
    print(f"Number of metrics: {summary['num_metrics']}")
    print(f"Overall average score: {summary['overall_average']}/10")
    
    # Display dataset statistics if available
    if "dataset_stats" in benchmark_result.metadata:
        stats = benchmark_result.metadata["dataset_stats"]
        print(f"\nDataset Statistics:")
        print(f"  Languages: {', '.join(stats.get('languages', {}).keys())}")
        print(f"  Average text length: {stats.get('average_text_length', 0):.1f} characters")
    
    print(f"\nAverage scores by metric:")
    for metric, score in summary['average_scores'].items():
        print(f"  {metric}: {score}/10")
    
    # Display score distribution if available
    if "score_distribution" in summary:
        dist = summary["score_distribution"]
        print(f"\nScore Distribution:")
        print(f"  Range: {dist['min']:.1f} - {dist['max']:.1f}")
        print(f"  Median: {dist['median']:.1f}")
        print(f"  Std Dev: {dist['std_dev']:.2f}")
    
    if export_path:
        print(f"\nResults exported to: {export_path}")
    if not args.skip_visualizations:
        print(f"Visualizations saved to: {args.results_dir}/")
        print(f"Interactive dashboard: {args.results_dir}/dashboard.html")
    
    print(f"\nDataset Loading Examples:")
    print(f"  # Load from JSON file:")
    print(f"  python3 run_benchmark.py --dataset-file my_questions.json")
    print(f"  # Load from CSV file:")
    print(f"  python3 run_benchmark.py --dataset-file questions.csv --text-column question")
    print(f"  # Use specific metrics:")
    print(f"  python3 run_benchmark.py --metrics relevance,hallucinations,bias")
    print(f"  # List available metrics:")
    print(f"  python3 run_benchmark.py --list-metrics")
    
    if export_path:
        print(f"\nTo re-use these results later:")
        print(f"  python3 run_benchmark.py --import-json {export_path}")
    
    if not args.skip_visualizations:
        print(f"\nTo view results:")
        print(f"  # Open interactive dashboard:")
        print(f"  open {args.results_dir}/dashboard.html")
        print(f"  # Or view static charts in: {args.results_dir}/")
    
    # Ensure database is disconnected
    if Database.is_connected():
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(main()) 