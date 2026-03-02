# LLM Benchmark Framework

A comprehensive toolkit for benchmarking and evaluating Large Language Models (LLMs) with multiple benchmark types, flexible datasets, and robust metrics—all accessible through a modern web dashboard.

## Features

- **Multiple Benchmark Types**:
  - **Standard Benchmarks**: Traditional Q&A evaluation with relevance, hallucinations, bias, fairness, and toxicity metrics
  - **RAG Benchmarks**: Retrieval-Augmented Generation evaluation with context-aware metrics
  - **Email Categorization**: Automated email classification accuracy testing
  - **MCP Tool Usage**: Model Context Protocol tool calling evaluation

- **Web Dashboard**: Vue.js frontend for managing benchmarks, datasets, and metrics
- **REST API**: FastAPI backend with MongoDB persistence
- **Flexible Datasets**: Load from JSON, CSV, YAML, or plain text
- **Model Factory**: One-line creation for OpenAI, Ollama, and custom models
- **Interactive Reports**: Automatic HTML reports with charts and analytics

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Docker (for MongoDB)
- [Ollama](https://ollama.ai/) (for running local LLMs)

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd llm_benchmark

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Start MongoDB

```bash
docker-compose up -d
```

This starts MongoDB in a Docker container with persistent storage.

### 3. Start the API Server

```bash
python3 run_api.py
```

The API will be available at `http://localhost:8000`

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:3000`

> **Note**: If you get a Node.js version error, see `frontend/UPGRADE_NODE.md` for upgrade instructions.

### 5. Pull Required Ollama Models

The benchmark framework uses Ollama models for both testing and evaluation. Make sure to pull the required models:

```bash
# Test model (can be changed in the UI)
ollama pull llama3.2:latest

# Default evaluator models
ollama pull deepseek-r1:1.5b
ollama pull gemma3:1b
```

---

## Using the Web Dashboard

The web dashboard is the primary interface for running benchmarks. It provides a user-friendly way to:

1. **Create and run benchmarks** with custom configurations
2. **Manage datasets** for different benchmark types
3. **Configure metrics** with custom evaluation criteria
4. **View results** with detailed visualizations

### Dashboard Tabs

#### Benchmarks Tab
- **Start New Benchmark**: Configure model, dataset, metrics, and evaluator models
- **View All Benchmarks**: See status, progress, and results of all benchmarks
- **Real-time Updates**: Auto-refresh for running benchmarks (every 5 seconds)

#### Settings Tab
- **Manage Datasets**: Import, edit, enable/disable datasets
- **Manage Metrics**: Create custom metrics, configure evaluation instructions
- **View Configurations**: See available models and settings

---

## Setting Up Test Data

Test data files are located in `.doc/test_data/` and can be imported via the web dashboard.

### Available Test Datasets

| File | Description | Benchmark Type |
|------|-------------|----------------|
| `email_categorisation_dataset.json` | 100 German university internship office emails | Email Categorization |
| `email_response_dataset.json` | Professional email response quality evaluation | Standard |
| `rag_email_dataset.json` | RAG benchmark with email queries and knowledge context | RAG |
| `mcp_test_dataset.json` | MCP tool usage scenarios (weather, mensa) | MCP |
| `weather_mcp_test_dataset.json` | Weather-specific MCP tool usage tests | MCP |

### Importing Datasets via Dashboard

1. Navigate to **Settings** tab
2. Click **Import Dataset**
3. Select the JSON file from `.doc/test_data/`
4. The dataset will be automatically parsed and stored in MongoDB

### Dataset Format Examples

#### Standard/RAG Dataset Format
```json
{
  "name": "My Dataset",
  "description": "Description of the dataset",
  "questions": [
    {
      "id": "q_001",
      "text": "Question text here",
      "context": "Optional context for RAG",
      "expected_answer": "Expected answer for evaluation"
    }
  ]
}
```

#### Email Categorization Dataset Format
```json
{
  "metadata": {
    "categories": {
      "category_a": 10,
      "category_b": 15
    }
  },
  "emails": [
    {
      "id": "email_001",
      "subject": "Email subject",
      "body": "Email body content",
      "expected_category": "category_a"
    }
  ]
}
```

---

## Setting Up Metrics

Metrics define how model responses are evaluated. The framework supports different metric types for each benchmark category.

### Creating Metrics via Dashboard

1. Navigate to **Settings** tab
2. Click **Create Metric**
3. Configure:
   - **Name**: Unique identifier (e.g., "relevance", "completeness")
   - **Type**: `standard`, `rag`, `mcp`, or `email_categorization`
   - **Evaluation Instructions**: Prompt template for evaluator models
   - **Scale**: Min/max values (default 0-10)

### Default Metric Types

#### Standard Metrics
- **Relevance**: How relevant is the response to the question
- **Completeness**: Does the response fully answer the question
- **Hallucination**: Detection of fabricated information
- **Bias**: Assessment of biased language or viewpoints

#### RAG Metrics
- **Context Relevance**: How well the context supports the answer
- **Faithfulness**: Is the answer grounded in the provided context
- **Answer Correctness**: Comparison with expected answer

#### Email Categorization Metrics
- **Accuracy**: Percentage of correctly categorized emails
- **Category Precision/Recall**: Per-category performance metrics

### Metric Configuration Example

```json
{
  "name": "relevance",
  "type": "standard",
  "description": "Evaluates how relevant the response is to the question",
  "evaluation_instructions": "Rate how relevant the response is to the question on a scale of 0-10. Consider whether the response directly addresses the question asked.",
  "scale_min": 0,
  "scale_max": 10
}
```

---

## Running Benchmarks

### Via Web Dashboard (Recommended)

1. Go to **Benchmarks** tab
2. Fill in the **Start New Benchmark** form:
   - **Model**: Select the model to test (e.g., `llama3.2:latest`)
   - **Model Base URL**: Ollama server URL (default: `http://localhost:11434`)
   - **Dataset**: Select from available datasets
   - **Metric Type**: Choose benchmark type (`standard`, `rag`, `mcp`, `email_categorization`)
   - **Evaluator Models**: Select models for evaluation (for standard/RAG)
3. Click **Start Benchmark**
4. Monitor progress in the benchmark list
5. Click **View Results** when completed

### Via Python Script

```python
from models.ollama_model import OllamaModel, OllamaConfig
from metrics import EvaluatorFactory
from dataset import DatasetLoader

# Create a model
model = OllamaModel(config=OllamaConfig(
    model_name="llama3.2:latest",
    temperature=0.5
))

# Load a dataset
dataset = DatasetLoader.from_json_file(".doc/test_data/rag_email_dataset.json")

# Create evaluator models
evaluator_models = [
    OllamaModel(config=OllamaConfig(model_name="deepseek-r1:1.5b")),
    OllamaModel(config=OllamaConfig(model_name="gemma3:1b"))
]
evaluator = EvaluatorFactory.create_evaluator(evaluator_models)

# Run benchmark
from benchmark.runner import BenchmarkRunner
from metrics import MetricFactory

metrics = MetricFactory.create_all_metrics()
runner = BenchmarkRunner(evaluator, metrics)

# Note: Use asyncio.run() for async execution
import asyncio
results = asyncio.run(runner.run_benchmark(model, dataset))
```

---

## API Reference

The REST API is available at `http://localhost:8000` when the server is running.

### Benchmarks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/benchmarks` | POST | Start a new benchmark |
| `/api/benchmarks` | GET | List all benchmarks |
| `/api/benchmarks/{id}` | GET | Get benchmark details |
| `/api/benchmarks/{id}/status` | GET | Get benchmark status |
| `/api/benchmarks/{id}/result` | GET | Get benchmark results |
| `/api/benchmarks/{id}` | DELETE | Delete a benchmark |

### Datasets

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/datasets` | GET | List all datasets |
| `/api/datasets` | POST | Create a new dataset |
| `/api/datasets/import` | POST | Import dataset from file |
| `/api/datasets/{id}` | GET | Get dataset details |
| `/api/datasets/{id}` | PUT | Update a dataset |
| `/api/datasets/{id}` | DELETE | Delete a dataset |

### Metrics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metrics` | GET | List all metrics |
| `/api/metrics` | POST | Create a new metric |
| `/api/metrics/{id}` | GET | Get metric details |
| `/api/metrics/{id}` | PUT | Update a metric |
| `/api/metrics/{id}` | DELETE | Delete a metric |

### Other

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models/list` | GET | List available Ollama models |
| `/health` | GET | Health check |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection URL |
| `MONGODB_DB_NAME` | `llm_benchmark` | Database name |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |

Create a `.env` file in the project root to override defaults:

```bash
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=llm_benchmark
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Project Structure

```
llm_benchmark/
├── api/                    # FastAPI REST API
│   └── main.py
├── benchmark/              # Benchmark runners
│   ├── runner.py
│   ├── email_benchmark_runner.py
│   └── rag_benchmark_runner.py
├── database/               # MongoDB models and repositories
├── dataset/                # Dataset loaders
├── frontend/               # Vue.js web dashboard
│   └── src/
│       └── components/
├── metrics/                # Evaluation metrics
├── models/                 # LLM model wrappers
├── .doc/
│   └── test_data/          # Sample test datasets
├── docker-compose.yml      # MongoDB Docker setup
├── requirements.txt        # Python dependencies
└── run_api.py              # API server entry point
```

---

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
docker ps

# Restart MongoDB
docker-compose down
docker-compose up -d
```

### Ollama Model Not Found
```bash
# List available models
ollama list

# Pull required model
ollama pull <model-name>
```

### Frontend Build Issues
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules
npm install
```

### API Server Errors
Check the terminal output for detailed error messages. Common issues:
- MongoDB not running
- Missing Python dependencies
- Port already in use (change in `.env`)

---

## Development

### Running Tests
```bash
pytest
```

### Linting
```bash
pip install -r requirements-dev.txt
flake8
mypy .
```

---

## License

[Add your license here]
