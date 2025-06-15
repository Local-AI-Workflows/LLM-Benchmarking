from llm_benchmark import evaluator_modelfrom llm_benchmark import evaluator

# LLM Benchmark Framework

A flexible framework for benchmarking and evaluating Large Language Models (LLMs) using multiple evaluator models and metrics.

## Overview

This framework allows you to:
- Evaluate LLM responses using multiple evaluator models
- Define custom evaluation metrics
- Run benchmarks across multiple prompts
- Visualize evaluation results
- Support for both OpenAI and Ollama models

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd llm_benchmark
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create a `.env` file):
```env
OPENAI_API_KEY=your_openai_api_key
```

## Usage

### Basic Benchmark Example

```python
import asyncio
from models.ollama_model import OllamaModel, OllamaConfig
from metrics.relevance import RelevanceMetric
from benchmark.runner import BenchmarkRunner
from visualizations.evaluation_visualizer import EvaluationVisualizer

async def main():
    # Initialize test model
    test_model = OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
    
    # Initialize metrics
    metrics = [RelevanceMetric()]
    
    evaluator_models = [
        OllamaModel(config=OllamaConfig(model_name="deepseek-r1:1.5b")),
        OllamaModel(config=OllamaConfig(model_name="gemma3:1b")),
        OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
    ]
    
    # Create benchmark runner
    runner = BenchmarkRunner(metrics, evaluator_models)
    
    # Define test prompts
    prompts = [
        "What is the capital of France?",
        "Explain the concept of quantum computing in simple terms.",
        "Write a short poem about artificial intelligence."
    ]
    
    # Get model responses
    model_responses = {}
    for prompt in prompts:
        response = await test_model.generate(prompt)
        model_responses[prompt] = response.text
    
    # Run benchmark
    benchmark_result = await runner.run_benchmark(prompts, model_responses)
    
    # Visualize results
    visualizer = EvaluationVisualizer(results_dir="results")
    figure = visualizer.plot_benchmark_results(benchmark_result, "Benchmark Results")
    visualizer.save_plot(figure, "benchmark_results.png")

if __name__ == "__main__":
    asyncio.run(main())
```

### Model Configuration

Both Ollama and OpenAI models can be configured using their respective config classes:

```python
# Ollama configuration
ollama_config = OllamaConfig(
    model_name="llama3.2:latest",
    temperature=0.7,
    num_ctx=2048
)
ollama_model = OllamaModel(config=ollama_config)

# OpenAI configuration
openai_config = OpenAIConfig(
    model_name="gpt-4",
    temperature=0.9,
    max_tokens=1000
)
openai_model = OpenAIModel(config=openai_config)
```

### Creating Custom Metrics

To create a custom metric, inherit from `BaseMetric`:

```python
from metrics.metric_base import BaseMetric
from metrics.responses import EvaluatorResponse

class CustomMetric(BaseMetric):
    def __init__(self):
        super().__init__("custom_metric", "Description of the metric")
    
    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator) -> EvaluatorResponse:
        # Implement your evaluation logic here
        evaluation = await evaluator.evaluate(prompt, response, self.name)
        return evaluation
```

## Components

### Models
- `BaseLLMModel`: Abstract base class for all LLM implementations
- `OllamaModel`: Implementation for local Ollama models
- `OpenAIModel`: Implementation for OpenAI models

### Metrics
- `BaseMetric`: Abstract base class for evaluation metrics
- `RelevanceMetric`: Implementation of relevance evaluation
- `BaseEvaluator`: Base class for model evaluators

### Benchmark
- `BenchmarkRunner`: Orchestrates the benchmark process using multiple evaluator models
  - Uses three local Ollama models (deepseek-r1:1.5b, gemma3:1b, llama3.2:latest) for evaluation
  - Aggregates results across multiple prompts and metrics

### Visualization
- `EvaluationVisualizer`: Generates plots for benchmark results
  - Overall benchmark results
  - Detailed metric comparisons
  - Results are saved to the `results` directory with timestamps