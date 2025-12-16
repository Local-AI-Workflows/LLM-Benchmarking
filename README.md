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

## REST API & Web Frontend

The project now includes a REST API backend and Vue.js frontend for managing benchmarks through a web interface.

### Setup

1. **Start MongoDB with Docker Compose**:
   ```bash
   docker-compose up -d
   ```
   This will start MongoDB in a Docker container with persistent storage.

2. **Configure Environment** (optional):
   ```bash
   # Create .env file (or use defaults)
   export MONGODB_URL=mongodb://localhost:27017
   export MONGODB_DB_NAME=llm_benchmark
   export API_HOST=0.0.0.0
   export API_PORT=8000
   ```

3. **Start the API Server**:
   ```bash
   python3 run_api.py
   ```
   The API will be available at `http://localhost:8000`

4. **Start the Frontend**:
   ```bash
   # Make sure you have Node.js 18+ (check with: node --version)
   cd frontend
   npm install
   npm run dev
   ```
   The frontend will be available at `http://localhost:3000`
   
   > **Note**: If you get a Node.js version error, see `frontend/UPGRADE_NODE.md` for upgrade instructions.

### API Endpoints

- `POST /api/benchmarks` - Start a new benchmark
- `GET /api/benchmarks` - List all benchmarks
- `GET /api/benchmarks/{id}` - Get benchmark details
- `GET /api/benchmarks/{id}/status` - Get benchmark status
- `GET /api/benchmarks/{id}/result` - Get benchmark results
- `DELETE /api/benchmarks/{id}` - Delete a benchmark
- `GET /api/metrics` - List available metrics
- `GET /health` - Health check

### Frontend Features

- Start new benchmark tests with custom configuration
- View all benchmarks with status indicators
- Real-time status updates (auto-refresh every 5 seconds)
- Visualize results with charts and tables
- View detailed benchmark information
- Delete benchmarks

## Documentation

Full guides, advanced configuration, and API reference are in the [`docs/`](docs/) folder and the `llm_benchmark.ipynb` notebook:
- Detailed metric definitions and configuration  
- Dataset formats and examples  
- Advanced CLI usage  
- Model-specific features for OpenAI and Ollama  