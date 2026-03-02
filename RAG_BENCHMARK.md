# RAG Benchmark Feature

This document describes the RAG (Retrieval-Augmented Generation) evaluation feature added to the LLM Benchmark system.

## Overview

The RAG benchmark evaluates how well LLMs use retrieved context to generate accurate, relevant, and well-written responses. This is essential for evaluating AI assistants that use knowledge bases or document retrieval.

## Evaluation Metrics

The RAG evaluation uses the following metrics (scored 1-5):

### 1. Faithfulness
- Measures whether the response stays true to the retrieved context
- Penalizes hallucinations and made-up facts
- **5** = All claims supported by context, **1** = Contradicts or fabricates

### 2. Relevance  
- Measures whether the response answers the user's question
- Evaluates if the response stays on topic
- **5** = Completely answers the question, **1** = Doesn't address the question

### 3. Language Quality
- Evaluates clarity, structure, and professionalism
- Checks if the response is well-organized
- **5** = Excellent writing, **1** = Incomprehensible

### 4. Grammatical Correctness
- Checks grammar, spelling, and punctuation
- Evaluates if language is simple and easy to understand
- **5** = Perfect grammar, **1** = Many errors

### 5. Overall RAG Score
- Holistic evaluation combining all dimensions
- Provides a single summary score
- **5** = Excellent overall, **1** = Poor overall

## Usage

### Via API

```bash
# Create a RAG benchmark
curl -X POST http://localhost:8000/api/benchmarks \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "llama3.2:latest",
    "metric_type": "rag",
    "dataset_id": "<your-rag-dataset-id>",
    "evaluator_models": [
      {"model_name": "llama3.2:latest"}
    ]
  }'
```

### Via CLI Script

```bash
# Run RAG benchmark with default settings
python run_rag_benchmark.py --model llama3.2:latest

# Run with custom dataset
python run_rag_benchmark.py \
  --model mistral:latest \
  --dataset rag_test_dataset.json \
  --output-dir results/rag_benchmark
```

### Initialize RAG Metrics in Database

```bash
# Create RAG metrics in MongoDB
python scripts/init_rag_metrics.py

# List existing RAG metrics
python scripts/init_rag_metrics.py list
```

## Dataset Format

RAG datasets should include context for each question:

```json
{
  "name": "RAG Knowledge Base QA",
  "description": "Test questions with reference context",
  "questions": [
    {
      "id": "rag_001",
      "text": "What is the return policy?",
      "context": "Our return policy allows returns within 30 days...",
      "expected_answer": "You can return items within 30 days...",
      "metadata": {
        "category": "customer_support"
      }
    }
  ]
}
```

## Frontend Dashboard

The RAG benchmark results are displayed with:

- **Overview cards**: Overall score, question count, metric count
- **Metric cards**: Individual scores for each RAG dimension
- **Radar chart**: Visual comparison of all metrics
- **Bar chart**: Average scores by metric
- **Detailed table**: Per-question evaluations
- **Expandable questions**: Full query, response, and rationale

## Architecture

### Files Created

- `metrics/rag_metrics.py` - RAG metric classes
- `benchmark/rag_benchmark_runner.py` - RAG-specific benchmark runner
- `frontend/src/components/RAGResults.vue` - Dashboard component
- `scripts/init_rag_metrics.py` - Database initialization
- `run_rag_benchmark.py` - CLI runner script
- `rag_test_dataset.json` - Sample test dataset

### Files Modified

- `database/models.py` - Added `MetricType.RAG`
- `metrics/__init__.py` - Exported RAG metrics
- `metrics/database_loader.py` - RAG metric loading
- `api/main.py` - RAG benchmark support
- `benchmark/__init__.py` - Export RAG runner
- `frontend/src/components/BenchmarkForm.vue` - RAG option
- `frontend/src/components/BenchmarkResultsView.vue` - RAG results

## Context Injection

For models without MCP/tool support, the benchmark can inject context directly into prompts:

```
Basierend auf dem folgenden Kontext, beantworte die Frage.

**Kontext:**
{retrieved_context}

**Frage:**
{user_query}

**Antwort:**
```

For MCP-enabled models, context is retrieved via tool calls and automatically captured in response metadata.

## Example Results

| Model | Faithfulness | Relevance | Language | Grammar | Overall |
|-------|-------------|-----------|----------|---------|---------|
| mistral-nemo | 3.9 | 4.1 | 4.0 | 4.2 | 3.8 |
| qwen | 3.4 | 3.6 | 3.5 | 3.7 | 3.2 |
| llama3.2 | 2.8 | 3.0 | 3.2 | 3.4 | 2.6 |

## Key Insights

> **Tool-Use alone is not enough** – The model's language capabilities significantly affect response quality. A model may successfully retrieve the right context but still fail to produce a good answer if it can't synthesize and communicate the information effectively.
