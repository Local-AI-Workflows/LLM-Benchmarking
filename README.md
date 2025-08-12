# LLM Benchmark Framework

A lightweight yet powerful toolkit for benchmarking and evaluating Large Language Models (LLMs) using multiple evaluator models, flexible datasets, and robust metrics.

## Features

- **Multiple Metrics**: Relevance, hallucinations, bias, fairness, robustness, toxicity  
- **Flexible Datasets**: Load from JSON, CSV, YAML, or plain text  
- **Model Factory**: One-line creation for OpenAI, Ollama, and custom models  
- **Interactive Dashboards**: Automatic HTML reports with charts and analytics  
- **Robust Validation & Logging**: Pydantic-based data checks, graceful error handling  

## Quick Start

### Install
```bash
git clone <repository-url>
cd llm_benchmark
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### Run a Sample Benchmark
```bash
python3 run_benchmark.py --dataset-sample
```

### Run with Custom Dataset
```bash
python3 run_benchmark.py --dataset-file my_questions.json --metrics relevance,bias
```

### Generate Dashboard
After running a benchmark:
```bash
open results/dashboard.html
```

## Example Usage

```python
from models.ollama_model import OllamaModel, OllamaConfig
from models import ModelFactory
from metrics import MetricFactory, EvaluatorFactory
from dataset import DatasetLoader

# Create a model
model = ModelFactory.create_ollama_model(model_name="llama3.2:latest", temperature=0.5)

# Load a dataset
dataset = DatasetLoader.load_from_file("questions.json")

# Evaluate
metrics = MetricFactory.create_all_metrics()
evaluator_models = [
        OllamaModel(config=OllamaConfig(model_name="deepseek-r1:1.5b")),
        OllamaModel(config=OllamaConfig(model_name="gemma3:1b")),
        OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
    ]
evaluator = EvaluatorFactory.create_evaluator(evaluator_models)

results = evaluator.run(dataset)

# Save results
results.save_to_json_file("results.json")
```
