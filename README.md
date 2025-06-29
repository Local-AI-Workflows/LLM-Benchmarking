from llm_benchmark import evaluator_modelfrom llm_benchmark import evaluator

# LLM Benchmark Framework

A comprehensive framework for benchmarking and evaluating Large Language Models (LLMs) using multiple evaluator models, flexible datasets, and robust evaluation metrics.

## Overview

This framework allows you to:
- Evaluate LLM responses using multiple evaluator models with enhanced reliability
- Load datasets from various formats (JSON, CSV, YAML, text files)
- Create structured question datasets with metadata
- Use a comprehensive set of evaluation metrics with factory-based creation
- Run benchmarks across multiple prompts with robust error handling
- Visualize evaluation results with detailed analytics
- Export/import benchmark results for reproducibility
- Support for both OpenAI and Ollama models

## Features

✅ **Enhanced Metrics System**: Factory-based metric creation with comprehensive validation
✅ **Robust Error Handling**: Graceful failure handling throughout the evaluation process
✅ **Rich Dataset Support**: Load questions from JSON, CSV, YAML, or plain text files
✅ **Question Metadata**: Context, instructions, expected answers, and custom metadata
✅ **Flexible Data Loading**: Auto-detection of file formats and custom column mapping
✅ **Advanced Filtering**: Filter datasets by text content or custom criteria
✅ **Result Export/Import**: Enhanced JSON serialization with Pydantic validation
✅ **Comprehensive Visualizations**: Multiple chart types with detailed breakdowns
✅ **Improved Logging**: Detailed logging throughout the evaluation process
✅ **Backward Compatibility**: Works with existing string-based prompts

## Available Metrics

The framework includes six comprehensive evaluation metrics:

- **Relevance**: Measures how well the response addresses the prompt's requirements
- **Hallucinations**: Detects fabricated or incorrect information in responses
- **Bias**: Evaluates demographic, cultural, or ideological bias
- **Fairness**: Assesses fair treatment of different groups and perspectives
- **Robustness**: Tests handling of edge cases, ambiguity, and challenging inputs
- **Toxicity**: Identifies harmful, toxic, or inappropriate content

Each metric includes:
- Enhanced score extraction with multiple patterns
- Configurable evaluation scales and formats
- Comprehensive error handling and validation
- Rich metadata tracking

## Enhanced Models System

The framework provides a comprehensive and robust models system with factory patterns, enhanced validation, and comprehensive error handling.

### Using the ModelFactory

```python
from models import ModelFactory

# List available model types
available = ModelFactory.list_available_models()
print(f"Available models: {available}")  # ['openai', 'ollama']

# Create models using the factory
ollama_model = ModelFactory.create_ollama_model(
    model_name="llama3.2:latest",
    temperature=0.7,
    base_url="http://localhost:11434"
)

openai_model = ModelFactory.create_openai_model(
    model_name="gpt-4",
    temperature=0.5,
    api_key="your-api-key"
)

# Create models from configuration dictionaries
configs = [
    {'type': 'ollama', 'model_name': 'llama3.2:latest', 'temperature': 0.7},
    {'type': 'openai', 'model_name': 'gpt-3.5-turbo', 'temperature': 0.5}
]
models = ModelFactory.create_models_from_configs(configs)

# Get model information
model_info = ModelFactory.get_model_info('ollama')
print(f"Model info: {model_info}")

# Validate configuration before creating
is_valid = ModelFactory.validate_model_config('ollama', {
    'model_name': 'test',
    'temperature': 0.7
})
```

### Enhanced Model Response

All models now return enhanced `ModelResponse` objects with comprehensive metadata:

```python
from models.responses import ModelResponse

# Generate response
response = await model.generate("What is artificial intelligence?")

# Access enhanced metadata
print(f"Response time: {response.response_time}s")
print(f"Token count: {response.token_count}")
print(f"Model used: {response.model_name}")
print(f"Success: {response.is_successful}")

# Add custom metadata
response.add_metadata("custom_field", "custom_value")

# Update usage statistics
response.update_usage_stats({"cost": 0.001, "tokens_per_second": 25})

# Get response summary
summary = response.get_summary()
print(f"Summary: {summary}")

# Serialize to/from dictionary
response_dict = response.to_dict()
restored_response = ModelResponse.from_dict(response_dict)

# Create error responses
error_response = ModelResponse.create_error_response(
    "API timeout",
    model_name="gpt-4"
)
```

### Enhanced Configuration

Model configurations now include comprehensive validation and utility methods:

```python
from models.model_config import OllamaConfig, OpenAIConfig

# Ollama configuration with validation
ollama_config = OllamaConfig(
    model_name="llama3.2:latest",
    base_url="http://localhost:11434",
    temperature=0.7,
    top_p=0.9,
    num_ctx=4096,
    stop=["</s>", "Human:"]
)

# OpenAI configuration with automatic API key detection
openai_config = OpenAIConfig(
    model_name="gpt-4",
    temperature=0.5,
    max_tokens=2000,
    frequency_penalty=0.1
)

# Get API parameters formatted for the provider
api_params = config.get_api_params()

# Get minimal parameters for health checks
health_params = config.get_health_check_params()

# Update configuration parameters
config.update_params(temperature=0.8, custom_param="value")

# Validate configuration
print(f"Has valid API key: {openai_config.has_valid_api_key()}")
```

### Enhanced Base Model Features

All models inherit enhanced functionality from the base class:

```python
# Performance tracking and statistics
stats = model.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Average response time: {stats['average_response_time']:.2f}s")

# Reset statistics
model.reset_stats()

# Health checking
health_status = await model.health_check()
print(f"Status: {health_status['status']}")
print(f"Response time: {health_status['response_time']:.2f}s")

# Model information
model_info = model.get_model_info()
print(f"Supported features: {model_info['supported_features']}")
print(f"Max context length: {model_info['max_context_length']}")

# Retry logic with exponential backoff
response = await model.generate_with_retry(
    "Test prompt",
    max_retries=3,
    retry_delay=1.0
)

# Batch processing
prompts = ["Question 1", "Question 2", "Question 3"]
responses = await model.batch_generate(prompts)
```

### Error Handling and Logging

The models system includes comprehensive error handling and logging:

```python
import logging

# Configure logging to see model operations
logging.basicConfig(level=logging.INFO)

# Automatic error handling with detailed logging
try:
    response = await model.generate("Test prompt")
except Exception as e:
    # Detailed error messages with context
    print(f"Generation failed: {e}")

# Error responses are automatically created for failed generations
if not response.is_successful:
    print(f"Error: {response.error}")
    print(f"Error metadata: {response.metadata}")
```

### Ollama-Specific Features

```python
from models import ModelFactory

ollama_model = ModelFactory.create_ollama_model(
    model_name="llama3.2:latest",
    base_url="http://localhost:11434"
)

# Check server availability
is_available = await ollama_model.check_server_availability()

# Get available models on the server
available_models = await ollama_model.get_available_models()
print(f"Available models: {available_models}")

# Ollama-specific configuration
config = OllamaConfig(
    model_name="llama3.2:latest",
    num_ctx=8192,  # Large context window
    stream=True,   # Enable streaming
    seed=42        # Reproducible generation
)
```

### OpenAI-Specific Features

```python
from models import ModelFactory

openai_model = ModelFactory.create_openai_model(
    model_name="gpt-4",
    temperature=0.7
)

# Automatic API key detection from environment
# Set OPENAI_API_KEY environment variable

# OpenAI-specific configuration
config = OpenAIConfig(
    model_name="gpt-4",
    max_tokens=2000,
    frequency_penalty=0.1,
    presence_penalty=0.1,
    stop=["Human:", "AI:"],
    seed=42  # Reproducible generation
)

# Get cost information
model_info = openai_model.get_model_info()
cost_info = model_info['cost_per_token']
print(f"Input cost: ${cost_info['input']}/1K tokens")
print(f"Output cost: ${cost_info['output']}/1K tokens")
```

### Model Registry and Discovery

```python
from models import get_all_models, get_model_by_name

# Get all available model classes
all_models = get_all_models()
print(f"Available model types: {list(all_models.keys())}")

# Get specific model class
OpenAIModel = get_model_by_name('openai')
OllamaModel = get_model_by_name('ollama')

# Create instances directly
model = OpenAIModel(config=OpenAIConfig(model_name="gpt-3.5-turbo"))
```

### JSON Serialization and Persistence

```python
# Enhanced response serialization
response_dict = response.to_dict()
json_str = json.dumps(response_dict, indent=2)

# Configuration serialization
config_dict = config.to_dict()
config_json = json.dumps(config_dict, indent=2)

# Automatic datetime handling
# Timestamps are automatically converted to ISO format
```

## Metrics System

### Using the MetricFactory

```python
from metrics import MetricFactory

# List available metrics
available = MetricFactory.list_available_metrics()
print(f"Available metrics: {available}")

# Create all metrics
all_metrics = MetricFactory.create_all_metrics()

# Create specific metrics
selected_metrics = MetricFactory.create_metrics_by_names(['relevance', 'bias'])

# Create individual metric with custom configuration
custom_metric = MetricFactory.create_metric('relevance')
```

### Custom Metric Configuration

```python
from metrics.metric_base import StandardMetric

class CustomMetric(StandardMetric):
    def __init__(self):
        super().__init__(
            name="custom_metric",
            description="A custom evaluation metric",
            evaluation_instructions="Your evaluation criteria here...",
            scale_min=1,  # Custom scale
            scale_max=5,
            additional_context="Additional context for evaluation"
        )
```

### Enhanced Error Handling

The metrics system now includes:
- Comprehensive validation using Pydantic models
- Graceful failure handling with detailed logging
- Score extraction with multiple patterns and fallbacks
- Automatic score validation and clamping
- Rich metadata tracking throughout the process

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

## Enhanced Results and Statistics

The framework now provides comprehensive statistics:

```python
# Get detailed summary statistics
stats = benchmark_result.get_summary_statistics()

print(f"Number of prompts: {stats['num_prompts']}")
print(f"Overall average: {stats['overall_average']}")
print(f"Score distribution: {stats['score_distribution']}")
print(f"Average scores by metric: {stats['average_scores']}")

# Get model-specific scores for a metric
model_scores = benchmark_result.get_model_scores_by_metric('relevance')
```

## Question Structure

The `Question` class supports rich metadata:

```python
from dataset import Question

question = Question(
    text="What is artificial intelligence?",
    context="You are explaining to a general audience",
    instructions="Use simple language and provide examples",
    expected_answer="AI is the simulation of human intelligence...",
    reference_answers=["AI mimics human thinking", "Artificial intelligence simulates cognition"],
    answer_key_points=["machine learning", "neural networks", "automation"],
    source="textbook",
    author="Dr. Johnson",
    metadata={"difficulty": "beginner", "topic": "AI"}
)
```

## Dataset Operations

### Loading and Filtering

```python
from dataset import DatasetLoader, Dataset

# Load from various formats
dataset = DatasetLoader.load_from_file("questions.json")  # Auto-detect
dataset = DatasetLoader.from_csv_file("data.csv", text_column="question")
dataset = DatasetLoader.from_yaml_file("questions.yaml")

# Filter by text content
filtered = dataset.filter_by_text("machine learning")

# Custom filtering
filtered = dataset.filter(lambda q: len(q.text) > 50)

# Sampling and shuffling
sample = dataset.sample(10, seed=42)
shuffled = dataset.shuffle(seed=42)

# Train/test splitting
train, test = dataset.split(train_ratio=0.8, seed=42)
```

### Dataset Statistics

```python
stats = dataset.get_statistics()
print(f"Number of questions: {stats['num_questions']}")
print(f"Languages: {stats['languages']}")
print(f"Average text length: {stats['average_text_length']}")
print(f"Sources: {stats['sources']}")
```

## Benchmark Results

### Enhanced JSON Export/Import

```python
# Export with robust serialization
benchmark_result.save_to_json_file("results.json")

# Import with validation
loaded_result = BenchmarkResult.load_from_json_file("results.json")

# Convert to/from JSON strings
json_str = benchmark_result.to_json()
loaded_result = BenchmarkResult.from_json(json_str)
```

### Combining Results

```python
# Combine results from multiple metrics
combined_result = BenchmarkResult.combine(
    [result1, result2, result3], 
    model_name="llama3.2:latest"
)
```

## Logging and Debugging

The framework includes comprehensive logging:

```python
import logging

# Configure logging to see detailed information
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Logs include:
# - Metric evaluation progress
# - Score extraction details
# - Error handling information
# - Performance insights
```

## Command Line Options

### Metric Selection

```bash
# List all available metrics
python3 run_benchmark.py --list-metrics

# Use specific metrics
python3 run_benchmark.py --metrics relevance,hallucinations,bias

# Use all metrics (default)
python3 run_benchmark.py
```

### Dataset Options

```bash
# Load from file with auto-detection
python3 run_benchmark.py --dataset-file data.json

# Force specific format
python3 run_benchmark.py --dataset-file data.csv --dataset-format csv

# Use sample dataset
python3 run_benchmark.py --dataset-sample

# CSV-specific options
python3 run_benchmark.py --dataset-file data.csv --text-column question
```

### Export/Import Options

```bash
# Export to specific file
python3 run_benchmark.py --export-json my_results.json

# Import existing results
python3 run_benchmark.py --import-json previous_results.json

# Skip visualizations
python3 run_benchmark.py --skip-visualizations

# Custom results directory
python3 run_benchmark.py --results-dir custom_results/
```

## Architecture

### Key Components

- **MetricFactory**: Factory for creating and discovering metrics
- **StandardMetric**: Enhanced base class with configurable evaluation
- **EvaluatorFactory**: Factory for creating single or multi-model evaluators
- **Enhanced Validation**: Pydantic models for robust data validation
- **Comprehensive Logging**: Detailed logging throughout the evaluation process
- **Error Handling**: Graceful failure handling with informative messages

### Metrics System Improvements

- **Reduced Code Duplication**: Simplified metric implementations
- **Enhanced Score Extraction**: Multiple patterns with automatic fallbacks
- **Configurable Scales**: Support for custom scoring scales (0-10, 1-5, etc.)
- **Rich Metadata**: Comprehensive tracking of evaluation context
- **Validation**: Automatic score validation and clamping
- **Logging**: Detailed debugging information

## File Structure

```
llm_benchmark/
├── metrics/
│   ├── __init__.py          # Enhanced module with factory and registry
│   ├── metric_base.py       # Enhanced base classes with configuration
│   ├── evaluator.py         # Improved evaluator with better error handling
│   ├── responses.py         # Pydantic models with validation
│   ├── relevance.py         # Simplified metric implementation
│   ├── hallucinations.py    # Simplified metric implementation
│   ├── bias.py              # Simplified metric implementation
│   ├── fairness.py          # Simplified metric implementation
│   ├── robustness.py        # Simplified metric implementation
│   └── toxicity.py          # Simplified metric implementation
├── dataset/
│   ├── __init__.py          # Dataset module exports
│   ├── question.py          # Question data structure
│   ├── dataset.py           # Dataset management
│   └── loaders.py           # Multi-format data loaders
├── models/                  # LLM model implementations
├── benchmark/               # Benchmark runner
├── visualizations/          # Result visualization
├── run_benchmark.py         # Enhanced CLI with metric selection
└── requirements.txt         # Updated dependencies
```

## Contributing

The metrics system is designed to be extensible. To add a new metric:

1. Create a new metric class inheriting from `StandardMetric`
2. Add it to the metric registry in `metrics/__init__.py`
3. Implement your evaluation instructions and any custom configuration

```python
from metrics.metric_base import StandardMetric

class MyCustomMetric(StandardMetric):
    def __init__(self):
        super().__init__(
            name="my_metric",
            description="Description of what this metric measures",
            evaluation_instructions="Detailed evaluation criteria...",
            scale_min=0,
            scale_max=10
        )
```

## Recent Improvements

### Metrics System Refactoring

- **Factory Pattern**: Centralized metric creation and discovery
- **Enhanced Validation**: Pydantic models for robust data validation
- **Improved Error Handling**: Graceful failures with detailed logging
- **Simplified Implementations**: Reduced code duplication across metrics
- **Better Score Extraction**: Multiple patterns with automatic fallbacks
- **Configurable Metrics**: Support for custom scales and formats
- **Rich Metadata**: Comprehensive tracking throughout evaluation
- **Enhanced JSON Support**: Robust serialization/deserialization

### Command Line Enhancements

- **Metric Selection**: Choose specific metrics or use all
- **Metric Discovery**: List available metrics with descriptions
- **Better Validation**: Comprehensive input validation with helpful errors
- **Enhanced Reporting**: Detailed statistics and score distributions

The framework now provides a more robust, maintainable, and user-friendly experience for LLM benchmarking with comprehensive error handling and detailed insights into model performance.

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
# List all available metrics
python3 run_benchmark.py --list-metrics

# Run benchmark with specific metrics
python3 run_benchmark.py --metrics relevance,bias,toxicity

# Run with built-in sample dataset
python3 run_benchmark.py --dataset-sample

# Load questions from a JSON file with specific metrics
python3 run_benchmark.py --dataset-file my_questions.json --metrics hallucinations,fairness

# Load from CSV with custom column mapping
python3 run_benchmark.py --dataset-file questions.csv --text-column question

# Import and re-analyze existing results
python3 run_benchmark.py --import-json results/benchmark_results_20241229_120000.json
```

### Programmatic Usage with Enhanced Features

```python
import asyncio
from models import ModelFactory
from metrics import MetricFactory, EvaluatorFactory
from benchmark.runner import BenchmarkRunner
from dataset import DatasetLoader

async def main():
    # Load dataset from file (auto-detects format)
    dataset = DatasetLoader.load_from_file("my_questions.json")
    
    # Or create from string list (backward compatibility)
    prompts = ["What is AI?", "Explain quantum computing."]
    dataset = DatasetLoader.from_strings(prompts, name="Simple Questions")
    
    # Initialize models using the enhanced ModelFactory
    test_model = ModelFactory.create_ollama_model(
        model_name="llama3.2:latest",
        temperature=0.7
    )
    
    evaluator_models = [
        ModelFactory.create_ollama_model(model_name="deepseek-r1:1.5b"),
        ModelFactory.create_ollama_model(model_name="gemma3:1b")
    ]
    evaluator = EvaluatorFactory.create_evaluator(evaluator_models)

    # Create metrics using the enhanced factory
    metrics = MetricFactory.create_all_metrics()  # All metrics
    # Or select specific metrics:
    # metrics = MetricFactory.create_metrics_by_names(['relevance', 'bias'])
    
    # Run benchmark with enhanced error handling and logging
    runner = BenchmarkRunner(evaluator, metrics)
    result = await runner.run_benchmark(test_model, dataset)
    
    # Get comprehensive statistics
    stats = result.get_summary_statistics()
    print(f"Overall average: {stats['overall_average']}")
    print(f"Score distribution: {stats['score_distribution']}")
    
    # Export results with enhanced JSON serialization
    result.save_to_json_file("my_benchmark_results.json")

if __name__ == "__main__":
    asyncio.run(main())
```

### Models System Enhancements (New)

**🏭 Factory Pattern Implementation**
- `ModelFactory` for centralized model creation and discovery
- Registry-based model discovery with `get_all_models()` and `get_model_by_name()`
- Convenient factory methods: `create_ollama_model()`, `create_openai_model()`
- Configuration validation with `validate_model_config()`
- Batch model creation from configuration dictionaries

**🔍 Enhanced ModelResponse with Pydantic Validation**
- Comprehensive validation with automatic error detection
- Enhanced metadata tracking (response time, token count, model info)
- Usage statistics tracking and cost analysis
- Error handling with `create_error_response()` factory method
- Robust JSON serialization/deserialization with datetime handling
- Response summaries and detailed metadata access

**⚙️ Improved Configuration System**
- Pydantic-based validation for all configuration parameters
- Automatic API key detection from environment variables
- Provider-specific parameter validation (OpenAI vs Ollama constraints)
- Health check parameter generation for testing
- Configuration update methods with validation
- Enhanced error messages with specific validation details

**🎯 Enhanced Base Model Functionality**
- Performance tracking with request counting and timing
- Success rate monitoring and error tracking
- Automatic retry logic with exponential backoff
- Health checking with detailed status reporting
- Batch processing capabilities for multiple prompts
- Model information and capability reporting
- Statistics tracking and reset functionality

**🔧 Comprehensive Error Handling**
- Graceful failure handling throughout the pipeline
- Detailed logging with structured information
- Provider-specific error handling (OpenAI API errors, Ollama connection issues)
- Error response creation with context preservation
- Validation errors with helpful messages
- Automatic error recovery and retry mechanisms

**📊 Enhanced Logging and Debugging**
- Structured logging throughout the models system
- Debug information for troubleshooting API calls
- Performance insights with timing information
- Request/response tracking with sanitized parameter logging
- Error logging with full context and stack traces
- Model availability and health status monitoring

### Key Benefits of All Improvements

**🚀 Reduced Code Duplication**
- Models: Eliminated duplicate response handling across providers
- Metrics: From ~200 lines per metric to ~20 lines with shared functionality

**🛡️ Better Error Handling**
- Comprehensive validation at all levels (input, processing, output)
- Graceful failure handling with detailed error messages
- Automatic error recovery and retry mechanisms

**🔍 Enhanced Usability**
- Easy model and metric discovery with factory patterns
- Intuitive APIs with comprehensive documentation
- Flexible configuration with validation

**🔧 Improved Reliability**
- Robust score extraction and validation
- Comprehensive testing and validation
- Performance tracking and monitoring

**🐛 Better Debugging**
- Comprehensive logging and metadata tracking
- Detailed error messages with context
- Performance insights and statistics

**⚡ Flexible Configuration**
- Customizable scales, formats, and contexts
- Provider-specific parameter validation
- Easy parameter updates with validation

**📈 Consistent Behavior**
- All models and metrics follow the same patterns
- Standardized error handling and logging
- Unified response formats and metadata

**📊 Enhanced Reporting**
- Rich statistics and analysis capabilities
- Comprehensive metadata tracking
- Better visualization and export options

### Backward Compatibility

All improvements maintain full backward compatibility:
- Existing model creation code continues to work
- Original metric implementations remain functional
- Previous configuration formats are still supported
- Existing benchmark results can be imported and analyzed

The framework now provides a significantly more robust, maintainable, and user-friendly experience for LLM benchmarking with comprehensive error handling, detailed insights, and professional-grade reliability.

## Summary

The LLM Benchmark Framework has been significantly enhanced with comprehensive improvements to both the metrics and models systems. These improvements provide:

- **Professional-grade reliability** with comprehensive error handling
- **Enhanced usability** with factory patterns and intuitive APIs
- **Better debugging capabilities** with structured logging and detailed metadata
- **Improved maintainability** with reduced code duplication and consistent patterns
- **Flexible configuration** with validation and provider-specific optimizations
- **Rich analytics** with performance tracking and comprehensive statistics

The framework is now ready for production use with enterprise-grade features while maintaining the simplicity and flexibility that makes it accessible for research and development.