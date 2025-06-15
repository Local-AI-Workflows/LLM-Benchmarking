import asyncio
from models.ollama_model import OllamaModel, OllamaConfig
from metrics.relevance import RelevanceMetric
from benchmark.runner import BenchmarkRunner
from visualizations.evaluation_visualizer import EvaluationVisualizer


async def main():
    # Initialize a test model (we'll use llama3.2 as our test model)
    test_model = OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
    
    # Initialize metrics
    metrics = [RelevanceMetric()]
    
    # Create benchmark runner
    runner = BenchmarkRunner(metrics)
    
    # Test prompts
    prompts = [
        "What is the capital of France?",
        "Explain the concept of quantum computing in simple terms.",
        "Write a short poem about artificial intelligence."
    ]
    
    # Get responses from the test model
    print("Getting responses from test model...")
    model_responses = {}
    for prompt in prompts:
        print(f"\nProcessing prompt: {prompt}")
        response = await test_model.generate(prompt)
        model_responses[prompt] = response.text
        print(f"Response: {response.text[:100]}...")
    
    # Run benchmark
    print("\nRunning benchmark...")
    benchmark_result = await runner.run_benchmark(prompts, model_responses)
    
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