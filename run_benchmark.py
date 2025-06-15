import asyncio
from models.ollama_model import OllamaModel, OllamaConfig
from metrics.relevance import RelevanceMetric
from metrics.evaluator import EvaluatorFactory
from benchmark.runner import BenchmarkRunner
from visualizations.evaluation_visualizer import EvaluationVisualizer


async def main():
    # Initialize the model to evaluate
    test_model = OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
    
    # Initialize evaluator model
    evaluator_model = OllamaModel(config=OllamaConfig(model_name="deepseek-r1:1.5b"))
    evaluator = EvaluatorFactory.create_evaluator([evaluator_model])
    
    # Initialize metrics
    metrics = [RelevanceMetric()]
    
    # Create benchmark runner
    runner = BenchmarkRunner(evaluator, metrics)
    
    # Test prompts
    prompts = [
        "What is the capital of France?",
        "Explain the concept of quantum computing in simple terms.",
        "Write a short poem about artificial intelligence."
    ]
    
    # Run benchmark
    print("\nRunning benchmark...")
    benchmark_result = await runner.run_benchmark(test_model, prompts)
    
    # Visualize results
    print("\nGenerating visualizations...")
    visualizer = EvaluationVisualizer(results_dir="results")
    
    # Plot overall results
    figure = visualizer.plot_benchmark_results(benchmark_result, "Local Ollama Models Benchmark")
    visualizer.save_plot(figure, "benchmark_results.png")
    
    # Plot detailed results for each metric
    for metric in metrics:
        figure = visualizer.plot_metric_details(benchmark_result, metric.name)
        visualizer.save_plot(figure, f"{metric.name}_details.png")
    
    print("\nBenchmark completed. Check the results directory for visualization files.")


if __name__ == "__main__":
    asyncio.run(main()) 