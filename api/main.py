"""FastAPI application for benchmark REST API."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging
import traceback

from database.connection import Database
from database.repository import BenchmarkRepository
from database.models import BenchmarkDocument, BenchmarkStatus
from metrics.responses import BenchmarkResult
from benchmark.runner import BenchmarkRunner
from metrics import MetricFactory, EvaluatorFactory
from models.ollama_model import OllamaModel, OllamaConfig
from dataset import DatasetLoader, Dataset

logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Benchmark API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize repository
repository = BenchmarkRepository()


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    await Database.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await Database.disconnect()


# Request/Response models
class BenchmarkCreateRequest(BaseModel):
    """Request model for creating a new benchmark."""
    model_name: str = "llama3.2:latest"
    dataset_file: Optional[str] = None
    dataset_format: Optional[str] = None
    metrics: Optional[List[str]] = None
    evaluator_models: Optional[List[str]] = None


class BenchmarkResponse(BaseModel):
    """Response model for benchmark data."""
    id: str
    status: str
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    model_name: Optional[str] = None
    dataset_name: Optional[str] = None
    metrics: List[str] = []
    evaluator_models: List[str] = []
    error_message: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class BenchmarkListResponse(BaseModel):
    """Response model for benchmark list."""
    benchmarks: List[BenchmarkResponse]
    total: int
    skip: int
    limit: int


class BenchmarkResultResponse(BaseModel):
    """Response model for benchmark results."""
    id: str
    status: str
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


def benchmark_doc_to_response(doc: BenchmarkDocument) -> BenchmarkResponse:
    """Convert BenchmarkDocument to BenchmarkResponse."""
    return BenchmarkResponse(
        id=str(doc.id),
        status=doc.status,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
        started_at=doc.started_at.isoformat() if doc.started_at else None,
        completed_at=doc.completed_at.isoformat() if doc.completed_at else None,
        model_name=doc.model_name,
        dataset_name=doc.dataset_name,
        metrics=doc.metrics,
        evaluator_models=doc.evaluator_models,
        error_message=doc.error_message,
        progress=doc.progress
    )


async def run_benchmark_task(benchmark_id: str, request: BenchmarkCreateRequest):
    """Background task to run a benchmark."""
    try:
        # Update status to running
        await repository.update_status(benchmark_id, BenchmarkStatus.RUNNING)
        
        # Load dataset
        dataset = None
        if request.dataset_file:
            if request.dataset_format:
                if request.dataset_format == 'json':
                    dataset = DatasetLoader.from_json_file(request.dataset_file)
                elif request.dataset_format == 'csv':
                    dataset = DatasetLoader.from_csv_file(request.dataset_file)
                elif request.dataset_format == 'yaml':
                    dataset = DatasetLoader.from_yaml_file(request.dataset_file)
                elif request.dataset_format == 'txt':
                    dataset = DatasetLoader.from_text_file(request.dataset_file)
            else:
                dataset = DatasetLoader.load_from_file(request.dataset_file)
        else:
            # Use default dataset
            from run_benchmark import create_default_dataset
            dataset = create_default_dataset()
        
        # Update dataset name
        await repository.update(benchmark_id, {"dataset_name": dataset.name})
        
        # Initialize model
        test_model = OllamaModel(config=OllamaConfig(model_name=request.model_name))
        
        # Initialize evaluator models
        if request.evaluator_models:
            evaluator_models = [
                OllamaModel(config=OllamaConfig(model_name=name))
                for name in request.evaluator_models
            ]
        else:
            evaluator_models = [
                OllamaModel(config=OllamaConfig(model_name="deepseek-r1:1.5b")),
                OllamaModel(config=OllamaConfig(model_name="gemma3:1b")),
                OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
            ]
        
        evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
        evaluator_model_names = [m.model_name for m in evaluator_models]
        
        # Initialize metrics
        if request.metrics:
            metrics = MetricFactory.create_metrics_by_names(request.metrics)
        else:
            metrics = MetricFactory.create_all_metrics()
        
        metric_names = [metric.name for metric in metrics]
        
        # Update benchmark with configuration
        await repository.update(benchmark_id, {
            "model_name": request.model_name,
            "metrics": metric_names,
            "evaluator_models": evaluator_model_names
        })
        
        # Run benchmark
        runner = BenchmarkRunner(evaluator, metrics)
        benchmark_result = await runner.run_benchmark(test_model, dataset)
        
        # Convert result to dict
        result_dict = benchmark_result.to_json()
        import json
        result_data = json.loads(result_dict)
        
        # Save result
        await repository.save_result(benchmark_id, result_data)
        
        logger.info(f"Benchmark {benchmark_id} completed successfully")
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Benchmark {benchmark_id} failed: {error_msg}\n{error_trace}")
        await repository.update_status(
            benchmark_id, 
            BenchmarkStatus.FAILED,
            error_message=error_msg,
            error_traceback=error_trace
        )


@app.post("/api/benchmarks", response_model=BenchmarkResponse, status_code=201)
async def create_benchmark(
    request: BenchmarkCreateRequest,
    background_tasks: BackgroundTasks
):
    """Create and start a new benchmark."""
    # Create benchmark document
    benchmark = BenchmarkDocument(
        status=BenchmarkStatus.PENDING,
        model_name=request.model_name,
        metrics=request.metrics or [],
        evaluator_models=request.evaluator_models or []
    )
    
    # Save to database
    benchmark_id = await repository.create(benchmark)
    
    # Start benchmark in background
    background_tasks.add_task(run_benchmark_task, benchmark_id, request)
    
    # Return created benchmark
    created_benchmark = await repository.get_by_id(benchmark_id)
    if not created_benchmark:
        raise HTTPException(status_code=500, detail="Failed to create benchmark")
    
    return benchmark_doc_to_response(created_benchmark)


@app.get("/api/benchmarks", response_model=BenchmarkListResponse)
async def list_benchmarks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """List all benchmarks."""
    benchmarks = await repository.get_all(skip=skip, limit=limit, status=status)
    total = await repository.count(status=status)
    
    return BenchmarkListResponse(
        benchmarks=[benchmark_doc_to_response(b) for b in benchmarks],
        total=total,
        skip=skip,
        limit=limit
    )


@app.get("/api/benchmarks/{benchmark_id}", response_model=BenchmarkResponse)
async def get_benchmark(benchmark_id: str):
    """Get a specific benchmark by ID."""
    benchmark = await repository.get_by_id(benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return benchmark_doc_to_response(benchmark)


@app.get("/api/benchmarks/{benchmark_id}/status", response_model=Dict[str, Any])
async def get_benchmark_status(benchmark_id: str):
    """Get the status of a benchmark."""
    benchmark = await repository.get_by_id(benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    
    return {
        "id": str(benchmark.id),
        "status": benchmark.status,
        "created_at": benchmark.created_at.isoformat(),
        "updated_at": benchmark.updated_at.isoformat(),
        "started_at": benchmark.started_at.isoformat() if benchmark.started_at else None,
        "completed_at": benchmark.completed_at.isoformat() if benchmark.completed_at else None,
        "progress": benchmark.progress,
        "error_message": benchmark.error_message
    }


@app.get("/api/benchmarks/{benchmark_id}/result", response_model=BenchmarkResultResponse)
async def get_benchmark_result(benchmark_id: str):
    """Get the result data of a completed benchmark."""
    benchmark = await repository.get_by_id(benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    
    if benchmark.status != BenchmarkStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"Benchmark is not completed. Current status: {benchmark.status}"
        )
    
    return BenchmarkResultResponse(
        id=str(benchmark.id),
        status=benchmark.status,
        result_data=benchmark.result_data,
        error_message=benchmark.error_message
    )


@app.delete("/api/benchmarks/{benchmark_id}", status_code=204)
async def delete_benchmark(benchmark_id: str):
    """Delete a benchmark."""
    success = await repository.delete(benchmark_id)
    if not success:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return None


@app.get("/api/metrics", response_model=List[Dict[str, str]])
async def list_available_metrics():
    """List all available metrics."""
    metrics = MetricFactory.list_available_metrics()
    result = []
    for metric_name in metrics:
        metric_class = MetricFactory.create_metric(metric_name)
        result.append({
            "name": metric_name,
            "description": metric_class.description
        })
    return result


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

