from llm_benchmark import evaluator_modelfrom llm_benchmark import evaluator

# LLM Benchmark Framework

A comprehensive framework for benchmarking and evaluating Large Language Models (LLMs) using multiple evaluator models, flexible datasets, and comprehensive metrics.

## Overview

This framework allows you to:
- Evaluate LLM responses using multiple evaluator models
- Load datasets from various formats (JSON, CSV, YAML, text files)
- Create structured question datasets with metadata
- Define custom evaluation metrics
- Run benchmarks across multiple prompts
- Visualize evaluation results with detailed analytics
- Export/import benchmark results for reproducibility
- Support for both OpenAI and Ollama models

## Features

✅ **Rich Dataset Support**: Load questions from JSON, CSV, YAML, or plain text files
✅ **Question Metadata**: Context, instructions, expected answers, and custom metadata
✅ **Flexible Data Loading**: Auto-detection of file formats and custom column mapping
✅ **Advanced Filtering**: Filter datasets by text content or custom criteria
✅ **Result Export/Import**: Save and load benchmark results in JSON format
✅ **Comprehensive Visualizations**: Multiple chart types with detailed breakdowns
✅ **Backward Compatibility**: Works with existing string-based prompts

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

## Quick Start

### Command Line Usage

```bash
# Run benchmark with built-in sample dataset
python3 run_benchmark.py --dataset-sample

# Load questions from a JSON file
python3 run_benchmark.py --dataset-file my_questions.json

# Load from CSV with custom column mapping
python3 run_benchmark.py --dataset-file questions.csv --text-column question

# Import and re-analyze existing results
python3 run_benchmark.py --import-json results/benchmark_results_20241229_120000.json
```

### Programmatic Usage

```python
import asyncio
from models.ollama_model import OllamaModel, OllamaConfig
from metrics.relevance import RelevanceMetric
from metrics.evaluator import EvaluatorFactory
from benchmark.runner import BenchmarkRunner
from dataset import DatasetLoader

async def main():
    # Load dataset from file (auto-detects format)
    dataset = DatasetLoader.load_from_file("my_questions.json")
    
    # Or create from string list (backward compatibility)
    prompts = ["What is AI?", "Explain quantum computing."]
    dataset = DatasetLoader.from_strings(prompts, name="Simple Questions")
    
    # Initialize models and metrics
    test_model = OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
    evaluator_models = [
        OllamaModel(config=OllamaConfig(model_name="deepseek-r1:1.5b")),
        OllamaModel(config=OllamaConfig(model_name="gemma3:1b"))
    ]
    evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
    metrics = [RelevanceMetric()]
    
    # Run benchmark
    runner = BenchmarkRunner(evaluator, metrics)
    result = await runner.run_benchmark(test_model, dataset)
    
    # Export results
    result.save_to_json_file("my_benchmark_results.json")

if __name__ == "__main__":
    asyncio.run(main())
```

## Dataset Formats

### 1. JSON Format

**Full Dataset Format:**
```json
{
  "name": "My Question Dataset",
  "description": "Custom questions for LLM evaluation",
  "questions": [
    {
      "id": "q001",
      "text": "What is machine learning?",
      "context": "You are explaining to a computer science student.",
      "instructions": "Provide a clear, technical explanation with examples.",
      "expected_answer": "Machine learning is a subset of AI that...",
      "reference_answers": ["ML is about algorithms learning from data"],
      "answer_key_points": ["supervised learning", "unsupervised learning", "algorithms"],
      "source": "textbook",
      "author": "Dr. Smith",
      "metadata": {
        "chapter": 5,
        "page": 142
      }
    }
  ]
}
```

**Simple Format:**
```json
{
  "questions": [
    "What is Python?",
    "Explain object-oriented programming.",
    {
      "text": "Write a sorting algorithm",
      "context": "Programming context",
      "instructions": "Use Python"
    }
  ]
}
```

### 2. CSV Format

```csv
text,expected_answer,context,instructions
"What is HTML?","HyperText Markup Language","","Technical explanation"
"Design a website layout","","You are a web designer","Be creative"
"Explain CSS selectors","","","Technical explanation needed"
```

**Load with custom columns:**
```bash
python3 run_benchmark.py --dataset-file data.csv --text-column question
```

### 3. YAML Format

```yaml
name: "Programming Questions"
description: "Questions about programming concepts"
questions:
  - text: "What is recursion?"
    context: "Computer science fundamentals"
    instructions: "Provide examples"
  
  - text: "Explain the difference between lists and dictionaries"
    context: "Python programming"
```

### 4. Plain Text Format

```
What is the capital of France?
Explain quantum computing in simple terms.
Write a Python function to calculate factorial.
What are the benefits of renewable energy?
```

```bash
python3 run_benchmark.py --dataset-file questions.txt
```

## Question Structure

The `Question` class supports rich metadata:

```python
from dataset import Question

question = Question(
    text="Explain machine learning",
    context="You are teaching a beginner",
    instructions="Use simple language with examples",
    expected_answer="Machine learning is...",
    reference_answers=["ML teaches computers to learn"],
    answer_key_points=["algorithms", "data", "patterns"],
    source="textbook",
    author="Dr. Smith",
    metadata={"version": "2.0"}
)
```

## Dataset Operations

### Loading Datasets

```python
from dataset import DatasetLoader

# Auto-detect format
dataset = DatasetLoader.load_from_file("questions.json")

# Specific format loaders
dataset = DatasetLoader.from_json_file("questions.json")
dataset = DatasetLoader.from_csv_file("questions.csv", text_column="question")
dataset = DatasetLoader.from_yaml_file("questions.yaml")
dataset = DatasetLoader.from_text_file("questions.txt")

# From string list
prompts = ["Question 1", "Question 2"]
dataset = DatasetLoader.from_strings(prompts, name="My Dataset")

# Sample dataset for testing
dataset = DatasetLoader.create_sample_dataset()
```

### Filtering and Manipulation

```python
# Custom filter function
long_questions = dataset.filter_questions(
    custom_filter=lambda q: len(q.text) > 100
)

# Text content search
python_questions = dataset.filter_questions(text_contains="python")

# Multiple criteria with custom filter
filtered = dataset.filter_questions(
    text_contains="programming",
    custom_filter=lambda q: q.expected_answer is not None
)
```

### Dataset Statistics

```python
stats = dataset.get_statistics()
print(f"Total questions: {stats['total_questions']}")
print(f"Languages: {stats['languages']}")
print(f"Average text length: {stats['average_text_length']:.1f}")
print(f"Questions with expected answers: {stats['has_expected_answers']}")
print(f"Questions with context: {stats['has_context']}")
```

### Sampling and Splitting

```python
# Random sample
sample = dataset.sample(10, random_seed=42)

# Train/test split
train, test = dataset.split(train_ratio=0.8, random_seed=42)

# Shuffle questions
shuffled = dataset.shuffle(random_seed=123)
```

## Model Configuration

### Ollama Models

```python
from models.ollama_model import OllamaModel, OllamaConfig

config = OllamaConfig(
    model_name="llama3.2:latest",
    temperature=0.7,
    num_ctx=2048
)
model = OllamaModel(config=config)
```

### OpenAI Models

```python
from models.openai_model import OpenAIModel, OpenAIConfig

config = OpenAIConfig(
    model_name="gpt-4",
    temperature=0.9,
    max_tokens=1000
)
model = OpenAIModel(config=config)
```

## Available Metrics

- **Relevance**: How well the response addresses the prompt
- **Hallucinations**: Presence of fabricated or incorrect information
- **Fairness**: Fair treatment of different groups and perspectives
- **Robustness**: Handling of edge cases and ambiguous inputs
- **Bias**: Presence of biased content or perspectives
- **Toxicity**: Harmful, toxic, or inappropriate content

## Custom Metrics

Create custom evaluation metrics:

```python
from metrics.metric_base import BaseMetric
from metrics.responses import EvaluatorResponse

class CustomMetric(BaseMetric):
    def __init__(self):
        super().__init__("custom_metric", "Description of the metric")
    
    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator) -> EvaluatorResponse:
        eval_prompt = f"""Evaluate this response for [your criteria]:
        
        Prompt: {prompt}
        Response: {response}
        
        Rate from 0-10 and provide rationale."""
        
        return await evaluator.evaluate(
            evaluation=eval_prompt,
            metric_name=self.name,
            metric_description=self.description
        )
```

## Result Export/Import

### Export Results

```python
# Export to JSON string
json_data = benchmark_result.to_json()

# Save to file
benchmark_result.save_to_json_file("results.json")
```

### Import Results

```python
# Import from JSON string
result = BenchmarkResult.from_json(json_data)

# Load from file
result = BenchmarkResult.load_from_json_file("results.json")
```

### Command Line Export/Import

```bash
# Results are automatically exported after running benchmarks
python3 run_benchmark.py --dataset-sample --export-json my_results.json

# Import and re-analyze existing results
python3 run_benchmark.py --import-json my_results.json --results-dir new_analysis
```

## Visualization

The framework automatically generates comprehensive visualizations:

- **Overall Results**: Bar charts comparing metrics across evaluator models
- **Per-Question Heatmaps**: Score matrices showing performance by question and evaluator
- **Model Summary**: Box plots and statistical summaries
- **Metric Details**: Distribution plots for individual metrics

All visualizations are saved to the `results` directory with timestamps.

## Command Line Options

```bash
# Dataset options
--dataset-file PATH          # Load dataset from file
--dataset-format FORMAT      # Force specific format (json/csv/yaml/txt)
--dataset-sample             # Use built-in sample dataset

# CSV-specific options
--text-column NAME           # Column containing question text

# Import/Export options
--import-json PATH           # Import existing results
--export-json PATH           # Export results to specific file
--results-dir DIR            # Directory for results and visualizations

# General options
--skip-visualizations        # Skip generating charts
```

## Examples

### Simple Question List

```python
prompts = [
    "What is the capital of France?",
    "Explain quantum computing.",
    "Write a Python function for sorting."
]
dataset = DatasetLoader.from_strings(prompts, name="Simple Questions")
```

### Rich Dataset with Metadata

```python
from dataset import Question

questions = [
    Question(
        text="What is machine learning?",
        context="Educational context",
        expected_answer="ML is a subset of AI...",
        instructions="Provide a clear explanation"
    ),
    Question(
        text="Write a sorting algorithm",
        context="Programming interview",
        instructions="Use Python and explain complexity"
    )
]
dataset = Dataset(questions, name="Custom Dataset")
```

### Filter and Sample

```python
# Load large dataset
dataset = DatasetLoader.load_from_file("large_dataset.json")

# Filter for questions containing specific terms
programming_questions = dataset.filter_questions(text_contains="programming")

# Sample 20 questions for quick testing
sample = programming_questions.sample(20, random_seed=42)

# Run benchmark
result = await runner.run_benchmark(model, sample)
```

## File Structure

```
llm_benchmark/
├── dataset/                 # Dataset management package
│   ├── __init__.py
│   ├── question.py         # Question data structure
│   ├── dataset.py          # Dataset collection management
│   └── loaders.py          # File format loaders
├── models/                 # LLM model implementations
├── metrics/                # Evaluation metrics
├── benchmark/              # Benchmark runner
├── visualizations/         # Result visualization
├── results/                # Generated results and charts
├── run_benchmark.py        # Main CLI script
└── requirements.txt        # Dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Your chosen license]