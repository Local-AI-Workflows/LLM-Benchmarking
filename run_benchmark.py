import asyncio
import argparse
import os
from datetime import datetime
from models.ollama_model import OllamaModel, OllamaConfig
from metrics.relevance import RelevanceMetric
from metrics.hallucinations import HallucinationsMetric
from metrics.fairness import FairnessMetric
from metrics.robustness import RobustnessMetric
from metrics.bias import BiasMetric
from metrics.toxicity import ToxicityMetric
from metrics.evaluator import EvaluatorFactory
from metrics.responses import BenchmarkResult
from benchmark.runner import BenchmarkRunner
from visualizations.evaluation_visualizer import EvaluationVisualizer
from dataset import DatasetLoader, Dataset, Question, QuestionCategory, QuestionDifficulty


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
        Question.from_string(prompts[0], category=QuestionCategory.FACTUAL, difficulty=QuestionDifficulty.EASY, tags=["geography"]),
        Question.from_string(prompts[1], category=QuestionCategory.REASONING, difficulty=QuestionDifficulty.MEDIUM, tags=["technology", "science"]),
        Question.from_string(prompts[2], category=QuestionCategory.CREATIVE, difficulty=QuestionDifficulty.MEDIUM, tags=["poetry", "ai"]),
        Question.from_string(prompts[3], category=QuestionCategory.MATHEMATICAL, difficulty=QuestionDifficulty.EASY, tags=["math", "calculation"]),
        Question.from_string(prompts[4], category=QuestionCategory.CODING, difficulty=QuestionDifficulty.MEDIUM, tags=["programming", "algorithms"])
    ]
    
    return Dataset(
        questions=questions,
        name="Default Benchmark Dataset",
        description="Standard test questions for LLM evaluation"
    )


async def run_new_benchmark(dataset: Dataset):
    """Run a new benchmark and return the results."""
    # Initialize the model to evaluate
    test_model = OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
    
    # Initialize evaluator models
    evaluator_models = [
        OllamaModel(config=OllamaConfig(model_name="deepseek-r1:1.5b")),
        OllamaModel(config=OllamaConfig(model_name="gemma3:1b")),
        OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
    ]
    evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
    
    # Initialize metrics
    metrics = [
        RelevanceMetric(),
        HallucinationsMetric(),
        FairnessMetric(),
        RobustnessMetric(),
        BiasMetric(),
        ToxicityMetric()
    ]
    
    # Create benchmark runner
    runner = BenchmarkRunner(evaluator, metrics)
    
    # Run benchmark with dataset
    print(f"\nRunning benchmark with dataset: {dataset.name}")
    print(f"Dataset description: {dataset.description}")
    print(f"Number of questions: {len(dataset)}")
    
    # Display dataset statistics
    stats = dataset.get_statistics()
    print(f"Categories: {list(stats['categories'].keys())}")
    print(f"Difficulties: {list(stats['difficulties'].keys())}")
    
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
                        text_column=args.text_column,
                        category_column=args.category_column,
                        difficulty_column=args.difficulty_column,
                        tags_column=args.tags_column
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
            print(f"❌ Failed to load dataset: {e}")
            print("Using default dataset instead...")
            return create_default_dataset()
    
    elif args.dataset_sample:
        print("Using sample dataset for demonstration...")
        return DatasetLoader.create_sample_dataset()
    
    else:
        print("Using default dataset...")
        return create_default_dataset()


def generate_visualizations(benchmark_result: BenchmarkResult, results_dir: str = "results"):
    """Generate and save visualizations for the benchmark results."""
    print(f"\nGenerating visualizations in '{results_dir}' directory...")
    
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)
    
    visualizer = EvaluationVisualizer(results_dir=results_dir)
    
    # Use dataset name in titles if available
    dataset_name = benchmark_result.metadata.get("dataset_name", "Dataset")
    title_suffix = f"using {dataset_name}"
    
    # Plot overall results
    figure = visualizer.plot_benchmark_results(benchmark_result, f"Benchmark Results {title_suffix}")
    visualizer.save_plot(figure, "benchmark_results.png")
    
    # Plot per-question scores
    figure = visualizer.plot_per_question_scores(benchmark_result)
    visualizer.save_plot(figure, "per_question_scores.png")
    
    # Plot model summary
    figure = visualizer.plot_model_summary(benchmark_result)
    visualizer.save_plot(figure, "model_summary.png")
    
    # Plot detailed results for each metric
    metrics = benchmark_result.metadata.get("metrics", [])
    for metric_name in metrics:
        figure = visualizer.plot_metric_details(benchmark_result, metric_name)
        visualizer.save_plot(figure, f"{metric_name}_details.png")


async def main():
    """Main function with command line argument support."""
    parser = argparse.ArgumentParser(description="LLM Benchmark Tool with Dataset Support")
    
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
    parser.add_argument(
        "--category-column",
        type=str,
        help="CSV column name containing question categories"
    )
    parser.add_argument(
        "--difficulty-column",
        type=str,
        help="CSV column name containing question difficulties"
    )
    parser.add_argument(
        "--tags-column",
        type=str,
        help="CSV column name containing question tags (comma-separated)"
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
    
    # Import existing results or run new benchmark
    if args.import_json:
        print(f"\nImporting benchmark results from: {args.import_json}")
        try:
            benchmark_result = BenchmarkResult.load_from_json_file(args.import_json)
            print("✓ Successfully imported benchmark results from JSON")
            
            # Display basic information about imported results
            num_prompts = len(benchmark_result.prompt_evaluations)
            avg_scores = benchmark_result.get_average_scores_by_metric()
            print(f"  - Number of prompts: {num_prompts}")
            print(f"  - Metrics: {', '.join(avg_scores.keys())}")
            print(f"  - Model: {benchmark_result.metadata.get('model_name', 'Unknown')}")
            print(f"  - Dataset: {benchmark_result.metadata.get('dataset_name', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Failed to import JSON file: {e}")
            return
    else:
        # Load dataset
        dataset = load_dataset(args)
        
        # Run new benchmark
        benchmark_result = await run_new_benchmark(dataset)
        print("✓ Benchmark completed successfully")
    
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
            print(f"❌ Failed to export to JSON file: {e}")
    
    # Generate visualizations unless skipped
    if not args.skip_visualizations:
        generate_visualizations(benchmark_result, args.results_dir)
        print(f"✓ Visualizations saved to '{args.results_dir}' directory")
    
    # Display summary
    print("\n" + "="*50)
    print("BENCHMARK SUMMARY")
    print("="*50)
    
    avg_scores = benchmark_result.get_average_scores_by_metric()
    print(f"Model: {benchmark_result.metadata.get('model_name', 'Unknown')}")
    print(f"Dataset: {benchmark_result.metadata.get('dataset_name', 'Unknown')}")
    print(f"Number of prompts: {len(benchmark_result.prompt_evaluations)}")
    print(f"Number of metrics: {len(avg_scores)}")
    
    # Display dataset statistics if available
    if "dataset_stats" in benchmark_result.metadata:
        stats = benchmark_result.metadata["dataset_stats"]
        print(f"\nDataset Statistics:")
        print(f"  Categories: {', '.join(stats.get('categories', {}).keys())}")
        print(f"  Difficulties: {', '.join(stats.get('difficulties', {}).keys())}")
        print(f"  Average text length: {stats.get('average_text_length', 0):.1f} characters")
    
    print("\nAverage scores by metric:")
    for metric, score in avg_scores.items():
        print(f"  {metric}: {score:.2f}/10")
    
    if export_path:
        print(f"\nResults exported to: {export_path}")
    if not args.skip_visualizations:
        print(f"Visualizations saved to: {args.results_dir}/")
    
    print("\nDataset Loading Examples:")
    print("  # Load from JSON file:")
    print("  python3 run_benchmark.py --dataset-file my_questions.json")
    print("  # Load from CSV file:")
    print("  python3 run_benchmark.py --dataset-file questions.csv --text-column question --category-column type")
    print("  # Use sample dataset:")
    print("  python3 run_benchmark.py --dataset-sample")
    
    if export_path:
        print(f"\nTo re-use these results later:")
        print(f"  python3 run_benchmark.py --import-json {export_path}")


if __name__ == "__main__":
    asyncio.run(main()) 