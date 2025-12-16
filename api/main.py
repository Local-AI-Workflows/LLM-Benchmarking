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
from database.metric_repository import MetricRepository
from database.dataset_repository import DatasetRepository
from database.models import (
    BenchmarkDocument, BenchmarkStatus, MetricDocument, 
    DatasetDocument, MetricType
)
from metrics.responses import BenchmarkResult
from benchmark.runner import BenchmarkRunner
from metrics import EvaluatorFactory
from metrics.metric_factory import MetricFactory
from models.ollama_model import OllamaModel, OllamaConfig
from models.ollama_mcp_model import OllamaWithMCPModel, OllamaMCPConfig, MCPServerConfig
from dataset import DatasetLoader, Dataset
from dataset.question import Question
import importlib

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

# Initialize repositories
repository = BenchmarkRepository()
metric_repository = MetricRepository()
dataset_repository = DatasetRepository()


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    await Database.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await Database.disconnect()


# Request/Response models
class MCPServerConfigRequest(BaseModel):
    """MCP server configuration."""
    name: str
    url: str
    description: Optional[str] = None
    available_tools: List[str] = []


class EvaluatorModelConfig(BaseModel):
    """Configuration for an evaluator model."""
    model_name: str
    base_url: Optional[str] = None


class BenchmarkCreateRequest(BaseModel):
    """Request model for creating a new benchmark."""
    model_name: str = "llama3.2:latest"
    model_base_url: Optional[str] = None  # Base URL for test model
    dataset_id: Optional[str] = None  # Use dataset from database
    metric_type: str = "standard"  # "standard", "mcp", or "email_categorization"
    metric_ids: List[str] = []  # Metric IDs from database
    evaluator_models: Optional[List[EvaluatorModelConfig]] = None  # Evaluator models with base URLs
    # MCP-specific
    mcp_tools: Optional[List[MCPServerConfigRequest]] = None
    # Email categorization specific
    instructional_prompts: Optional[List[str]] = None  # Instructional prompts for email categorization


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
    metric_type: Optional[str] = None
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
        dataset_name=doc.dataset_name or "Unknown Dataset",
        metric_type=doc.metric_type or "standard",
        metrics=doc.metrics,
        evaluator_models=doc.evaluator_models,
        error_message=doc.error_message,
        progress=doc.progress
    )


def load_metric_from_db(metric_doc: MetricDocument):
    """Load a metric instance from database document, using stored configuration."""
    # Use the database_loader function which handles class_path inference
    from metrics.database_loader import load_metric_from_db as db_load_metric
    return db_load_metric(metric_doc)


async def run_benchmark_task(benchmark_id: str, request: BenchmarkCreateRequest):
    """Background task to run a benchmark."""
    try:
        # Update status to running
        await repository.update_status(benchmark_id, BenchmarkStatus.RUNNING)
        
        # Load dataset from database
        dataset = None
        if request.dataset_id:
            dataset_doc = await dataset_repository.get_by_id(request.dataset_id)
            if not dataset_doc:
                raise ValueError(f"Dataset not found: {request.dataset_id}")
            if not dataset_doc.enabled:
                raise ValueError(f"Dataset is disabled: {request.dataset_id}")
            
            # Convert dataset document to Dataset object
            questions = [Question.from_dict(q_dict) for q_dict in dataset_doc.questions]
            dataset = Dataset(
                questions=questions,
                name=dataset_doc.name,
                description=dataset_doc.description
            )
            dataset.metadata = dataset_doc.metadata
        else:
            # Use first available dataset
            datasets = await dataset_repository.get_all(enabled_only=True, limit=1)
            if datasets:
                dataset_doc = datasets[0]
                questions = [Question.from_dict(q_dict) for q_dict in dataset_doc.questions]
                dataset = Dataset(
                    questions=questions,
                    name=dataset_doc.name,
                    description=dataset_doc.description
                )
                dataset.metadata = dataset_doc.metadata
            else:
                raise ValueError("No datasets available in database")
        
        # Update dataset name and ID
        await repository.update(benchmark_id, {
            "dataset_name": dataset.name,
            "dataset_id": request.dataset_id
        })
        
        # Initialize model (with MCP support if needed)
        test_model = None
        if request.metric_type == "mcp" and request.mcp_tools:
            # Create MCP server configs
            mcp_servers = [
                MCPServerConfig(
                    name=server.name,
                    url=server.url,
                    description=server.description or "",
                    available_tools=server.available_tools
                )
                for server in request.mcp_tools
            ]
            
            mcp_config = OllamaMCPConfig(
                model_name=request.model_name,
                base_url=request.model_base_url,
                temperature=0.7,
                timeout=300.0,
                num_ctx=8192,
                mcp_servers=mcp_servers,
                max_tool_calls=5,
                tool_call_timeout=30.0
            )
            test_model = OllamaWithMCPModel(config=mcp_config)
        else:
            # Only pass base_url if it's provided (not None)
            config_kwargs = {"model_name": request.model_name}
            if request.model_base_url:
                config_kwargs["base_url"] = request.model_base_url
            test_model = OllamaModel(config=OllamaConfig(**config_kwargs))
        
        # Initialize evaluator models (not needed for email categorization)
        if request.metric_type == MetricType.EMAIL_CATEGORIZATION:
            # Email categorization doesn't use evaluator models
            evaluator_models = []
            evaluator = None  # Will be passed but not used
            evaluator_model_names = []
        else:
            if request.evaluator_models:
                evaluator_models = [
                    OllamaModel(config=OllamaConfig(
                        model_name=eval_config.model_name,
                        **({"base_url": eval_config.base_url} if eval_config.base_url else {})
                    ))
                    for eval_config in request.evaluator_models
                ]
            else:
                evaluator_models = [
                    OllamaModel(config=OllamaConfig(model_name="deepseek-r1:1.5b")),
                    OllamaModel(config=OllamaConfig(model_name="gemma3:1b")),
                    OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
                ]
            
            evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
            evaluator_model_names = [m.model_name for m in evaluator_models]
        
        # Load metrics from database
        metrics = []
        metric_names = []
        metric_ids = []
        
        # For email categorization, automatically create metric if none provided
        if request.metric_type == MetricType.EMAIL_CATEGORIZATION:
            if request.metric_ids:
                # Use specified metrics if provided
                for metric_id in request.metric_ids:
                    metric_doc = await metric_repository.get_by_id(metric_id)
                    if not metric_doc:
                        raise ValueError(f"Metric not found: {metric_id}")
                    if metric_doc.type != request.metric_type:
                        logger.warning(f"Metric {metric_doc.name} type mismatch, skipping")
                        continue
                    
                    metric = load_metric_from_db(metric_doc)
                    metrics.append(metric)
                    metric_names.append(metric_doc.name)
                    metric_ids.append(metric_id)
            
            # If no metrics found, create one automatically
            if not metrics:
                from metrics.email_categorization_metric import EmailCategorizationMetric
                
                # Extract categories from dataset metadata if available
                categories = None
                if dataset and hasattr(dataset, 'metadata') and dataset.metadata:
                    categories_dict = dataset.metadata.get('categories', {})
                    if categories_dict:
                        categories = list(categories_dict.keys())
                    # Also try to extract from questions
                    if not categories and dataset.questions:
                        categories = list(set([
                            q.expected_answer for q in dataset.questions 
                            if q.expected_answer
                        ]))
                
                # Create email categorization metric
                email_metric = EmailCategorizationMetric(
                    name="email_categorization",
                    description="Email categorization accuracy metric",
                    categories=categories
                )
                metrics.append(email_metric)
                metric_names.append("email_categorization")
                metric_ids.append("auto-generated")
                logger.info(f"Auto-created email categorization metric with categories: {categories}")
        else:
            # Standard metric loading for other types
            if request.metric_ids:
                for metric_id in request.metric_ids:
                    metric_doc = await metric_repository.get_by_id(metric_id)
                    if not metric_doc:
                        raise ValueError(f"Metric not found: {metric_id}")
                    if not metric_doc.enabled:
                        logger.warning(f"Metric {metric_doc.name} is disabled, skipping")
                        continue
                    if metric_doc.type != request.metric_type:
                        logger.warning(f"Metric {metric_doc.name} type mismatch, skipping")
                        continue
                    
                    metric = load_metric_from_db(metric_doc)
                    metrics.append(metric)
                    metric_names.append(metric_doc.name)
                    metric_ids.append(metric_id)
            else:
                # Load all enabled metrics of the specified type
                metric_docs = await metric_repository.get_all(
                    metric_type=request.metric_type,
                    enabled_only=True
                )
                for metric_doc in metric_docs:
                    metric = load_metric_from_db(metric_doc)
                    metrics.append(metric)
                    metric_names.append(metric_doc.name)
                    metric_ids.append(str(metric_doc.id))
            
            if not metrics:
                raise ValueError(f"No enabled {request.metric_type} metrics found")
        
        # Update benchmark with configuration
        mcp_tools_dict = None
        if request.mcp_tools:
            mcp_tools_dict = [tool.model_dump() for tool in request.mcp_tools]
        
        await repository.update(benchmark_id, {
            "model_name": request.model_name,
            "metrics": metric_names,
            "metric_ids": metric_ids,
            "metric_type": request.metric_type,
            "evaluator_models": evaluator_model_names,
            "mcp_tools": mcp_tools_dict
        })
        
        # Run benchmark
        # For email categorization with instructional prompts, use specialized runner
        if request.metric_type == MetricType.EMAIL_CATEGORIZATION:
            from benchmark.email_benchmark_runner import EmailBenchmarkRunner
            email_runner = EmailBenchmarkRunner(metrics)
            
            # Use provided prompts or default prompt
            instructional_prompts = request.instructional_prompts or [
                "Categorize the following email into one of these categories: contract_submission, international_office_question, internship_postponement, uncategorized. Respond with only the category name."
            ]
            
            results_by_prompt = await email_runner.run_benchmark_with_prompts(
                test_model,
                dataset,
                instructional_prompts
            )
            
            # Combine results from all prompts
            # Get the best prompt for metadata
            best_prompt = email_runner.get_best_prompt(results_by_prompt)
            
            # Combine all prompt_evaluations from all prompts
            all_prompt_evaluations = []
            for prompt, result in results_by_prompt.items():
                # Add all prompt evaluations from this prompt
                # Each result contains evaluations for all emails with this prompt
                logger.info(f"Adding {len(result.prompt_evaluations)} prompt evaluations from prompt (index {results_by_prompt[prompt].metadata.get('instructional_prompt_index', 'unknown')})")
                all_prompt_evaluations.extend(result.prompt_evaluations)
            
            expected_total = len(instructional_prompts) * len(dataset.questions) if dataset else 0
            logger.info(f"Total prompt evaluations after combining: {len(all_prompt_evaluations)} (expected: {expected_total})")
            
            if len(all_prompt_evaluations) != expected_total:
                logger.warning(f"Mismatch in prompt evaluations count! Got {len(all_prompt_evaluations)}, expected {expected_total}")
                logger.warning(f"Prompts: {len(instructional_prompts)}, Questions: {len(dataset.questions) if dataset else 0}")
                for prompt, result in results_by_prompt.items():
                    logger.warning(f"  Prompt '{prompt[:50]}...' has {len(result.prompt_evaluations)} evaluations")
            
            # Calculate overall stats from all prompts
            total_emails = len(dataset.questions) if dataset else 0
            best_result = results_by_prompt[best_prompt]
            
            # Create a combined benchmark result with all prompt evaluations
            from metrics.responses import BenchmarkResult
            benchmark_result = BenchmarkResult(
                prompt_evaluations=all_prompt_evaluations,
                metadata={
                    "model_name": test_model.model_name,
                    "num_prompts": len(instructional_prompts),
                    "num_metrics": 1,
                    "metrics": ["email_categorization"],
                    "evaluator_models": [],
                    "accuracy_percentage": best_result.metadata.get("accuracy_percentage", 0.0),
                    "correct_count": best_result.metadata.get("correct_count", 0),
                    "total_count": total_emails  # Total emails (same for all prompts)
                }
            )
            
            # Add information about all prompts to metadata
            prompt_accuracies = {
                prompt: result.metadata.get("accuracy_percentage", 0.0)
                for prompt, result in results_by_prompt.items()
            }
            benchmark_result.metadata["all_prompt_results"] = prompt_accuracies
            benchmark_result.metadata["best_prompt"] = best_prompt
        else:
            # Standard benchmark runner
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
    # Validate metric type
    if request.metric_type not in [MetricType.STANDARD, MetricType.MCP, MetricType.EMAIL_CATEGORIZATION]:
        raise HTTPException(status_code=400, detail="metric_type must be 'standard', 'mcp', or 'email_categorization'")
    
    # Validate dataset exists if provided
    if request.dataset_id:
        dataset = await dataset_repository.get_by_id(request.dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset not found: {request.dataset_id}")
        if not dataset.enabled:
            raise HTTPException(status_code=400, detail=f"Dataset is disabled: {request.dataset_id}")
    
    # Validate metrics exist if provided
    if request.metric_ids:
        for metric_id in request.metric_ids:
            metric = await metric_repository.get_by_id(metric_id)
            if not metric:
                raise HTTPException(status_code=404, detail=f"Metric not found: {metric_id}")
            if not metric.enabled:
                raise HTTPException(status_code=400, detail=f"Metric is disabled: {metric_id}")
            if metric.type != request.metric_type:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Metric {metric.name} type mismatch: expected {request.metric_type}, got {metric.type}"
                )
    
    # Create benchmark document
    mcp_tools_dict = None
    if request.mcp_tools:
        mcp_tools_dict = [tool.dict() for tool in request.mcp_tools]
    
    # Extract model names from EvaluatorModelConfig objects
    evaluator_model_names = []
    if request.evaluator_models:
        evaluator_model_names = [model.model_name for model in request.evaluator_models]
    
    benchmark = BenchmarkDocument(
        status=BenchmarkStatus.PENDING,
        model_name=request.model_name,
        dataset_id=request.dataset_id,
        metric_type=request.metric_type,
        metric_ids=request.metric_ids,
        evaluator_models=evaluator_model_names,
        mcp_tools=mcp_tools_dict
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
    try:
        benchmark = await repository.get_by_id(benchmark_id)
        if not benchmark:
            logger.warning(f"Benchmark not found: {benchmark_id}")
            raise HTTPException(status_code=404, detail=f"Benchmark not found: {benchmark_id}")
        return benchmark_doc_to_response(benchmark)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving benchmark {benchmark_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving benchmark: {str(e)}")


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


# Metrics endpoints
class MetricCreateRequest(BaseModel):
    """Request model for creating a metric."""
    name: str
    type: str  # "standard" or "mcp"
    description: str = ""
    enabled: bool = True
    metadata: Dict[str, Any] = {}
    # Metric configuration
    evaluation_instructions: str = ""
    scale_min: int = 0
    scale_max: int = 10
    custom_format: Optional[str] = None
    additional_context: Optional[str] = None
    # Note: class_path is auto-generated from name/type, not user-editable


class MetricUpdateRequest(BaseModel):
    """Request model for updating a metric."""
    description: Optional[str] = None
    enabled: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    # Metric configuration
    evaluation_instructions: Optional[str] = None
    scale_min: Optional[int] = None
    scale_max: Optional[int] = None
    custom_format: Optional[str] = None
    additional_context: Optional[str] = None
    # Note: name and class_path cannot be changed after creation


class MetricResponse(BaseModel):
    """Response model for metric data."""
    id: str
    name: str
    type: str
    description: str
    class_path: Optional[str] = None  # DEPRECATED: No longer stored, inferred automatically
    enabled: bool
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = {}
    # Metric configuration
    evaluation_instructions: str = ""
    scale_min: int = 0
    scale_max: int = 10
    custom_format: Optional[str] = None
    additional_context: Optional[str] = None


def metric_doc_to_response(doc: MetricDocument) -> MetricResponse:
    """Convert MetricDocument to MetricResponse."""
    return MetricResponse(
        id=str(doc.id),
        name=doc.name,
        type=doc.type,
        description=doc.description,
        class_path=doc.class_path,  # May be None, will be inferred automatically
        enabled=doc.enabled,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
        metadata=doc.metadata,
        evaluation_instructions=doc.evaluation_instructions,
        scale_min=doc.scale_min,
        scale_max=doc.scale_max,
        custom_format=doc.custom_format,
        additional_context=doc.additional_context
    )


@app.get("/api/metrics", response_model=List[MetricResponse])
async def list_metrics(
    metric_type: Optional[str] = None,
    enabled_only: bool = False
):
    """List all metrics."""
    metrics = await metric_repository.get_all(
        metric_type=metric_type,
        enabled_only=enabled_only
    )
    return [metric_doc_to_response(m) for m in metrics]


@app.get("/api/metrics/{metric_id}", response_model=MetricResponse)
async def get_metric(metric_id: str):
    """Get a specific metric by ID."""
    metric = await metric_repository.get_by_id(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric_doc_to_response(metric)


def get_class_path_for_metric(name: str, metric_type: str) -> Optional[str]:
    """Get class path for a metric based on name and type.
    
    DEPRECATED: class_path is no longer needed. We use GenericMetric for all metrics.
    This function is kept for backwards compatibility only.
    """
    # Return None - we don't need class_path anymore
    return None


@app.post("/api/metrics", response_model=MetricResponse, status_code=201)
async def create_metric(request: MetricCreateRequest):
    """Create a new metric."""
    if request.type not in [MetricType.STANDARD, MetricType.MCP, MetricType.EMAIL_CATEGORIZATION]:
        raise HTTPException(status_code=400, detail="Type must be 'standard', 'mcp', or 'email_categorization'")
    
    # Check if name already exists
    existing = await metric_repository.get_by_name(request.name)
    if existing:
        raise HTTPException(status_code=400, detail="Metric with this name already exists")
    
    # No need to validate class_path - we use GenericMetric for all metrics
    # Just validate that the name follows the expected pattern
    if not request.name or len(request.name.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Metric name cannot be empty"
        )
    
    # Convert request to metric data
    metric_data = request.model_dump()
    # Don't store class_path - it's inferred automatically when loading
    
    # If evaluation_instructions is empty, that's fine - user can add it later
    # We no longer try to get defaults from metric classes since we use GenericMetric
    # All configuration comes from the database
    
    metric = MetricDocument(**metric_data)
    metric_id = await metric_repository.create(metric)
    
    created_metric = await metric_repository.get_by_id(metric_id)
    if not created_metric:
        raise HTTPException(status_code=500, detail="Failed to create metric")
    
    return metric_doc_to_response(created_metric)


@app.put("/api/metrics/{metric_id}", response_model=MetricResponse)
async def update_metric(metric_id: str, request: MetricUpdateRequest):
    """Update a metric."""
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    success = await metric_repository.update(metric_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Metric not found")
    
    updated_metric = await metric_repository.get_by_id(metric_id)
    return metric_doc_to_response(updated_metric)


@app.delete("/api/metrics/{metric_id}", status_code=204)
async def delete_metric(metric_id: str):
    """Delete a metric."""
    success = await metric_repository.delete(metric_id)
    if not success:
        raise HTTPException(status_code=404, detail="Metric not found")
    return None


# Dataset endpoints
class DatasetCreateRequest(BaseModel):
    """Request model for creating a dataset."""
    name: str
    description: str = ""
    questions: List[Dict[str, Any]] = []
    enabled: bool = True
    metadata: Dict[str, Any] = {}


class DatasetUpdateRequest(BaseModel):
    """Request model for updating a dataset."""
    name: Optional[str] = None
    description: Optional[str] = None
    questions: Optional[List[Dict[str, Any]]] = None
    enabled: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class DatasetResponse(BaseModel):
    """Response model for dataset data."""
    id: str
    name: str
    description: str
    questions: List[Dict[str, Any]] = []
    enabled: bool
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = {}


def dataset_doc_to_response(doc: DatasetDocument) -> DatasetResponse:
    """Convert DatasetDocument to DatasetResponse."""
    return DatasetResponse(
        id=str(doc.id),
        name=doc.name,
        description=doc.description,
        questions=doc.questions,
        enabled=doc.enabled,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
        metadata=doc.metadata
    )


@app.get("/api/datasets", response_model=List[DatasetResponse])
async def list_datasets(enabled_only: bool = False):
    """List all datasets."""
    datasets = await dataset_repository.get_all(enabled_only=enabled_only)
    return [dataset_doc_to_response(d) for d in datasets]


@app.get("/api/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str):
    """Get a specific dataset by ID."""
    dataset = await dataset_repository.get_by_id(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset_doc_to_response(dataset)


@app.post("/api/datasets", response_model=DatasetResponse, status_code=201)
async def create_dataset(request: DatasetCreateRequest):
    """Create a new dataset."""
    # Check if name already exists
    existing = await dataset_repository.get_by_name(request.name)
    if existing:
        raise HTTPException(status_code=400, detail="Dataset with this name already exists")
    
    dataset = DatasetDocument(**request.model_dump())
    dataset_id = await dataset_repository.create(dataset)
    
    created_dataset = await dataset_repository.get_by_id(dataset_id)
    if not created_dataset:
        raise HTTPException(status_code=500, detail="Failed to create dataset")
    
    return dataset_doc_to_response(created_dataset)


class DatasetImportRequest(BaseModel):
    """Request model for importing a dataset."""
    file_content: str
    file_format: str = "json"
    name: Optional[str] = None


@app.post("/api/datasets/import", response_model=DatasetResponse, status_code=201)
async def import_dataset(request: DatasetImportRequest):
    """Import a dataset from file content."""
    import tempfile
    import os
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{request.file_format}', delete=False) as f:
        f.write(request.file_content)
        temp_path = f.name
    
    try:
        # Load dataset
        if request.file_format == 'json':
            # Try email format first, then fall back to standard format
            try:
                from dataset.email_loader import EmailDatasetLoader
                dataset = EmailDatasetLoader.from_json_file(temp_path)
            except (ValueError, KeyError):
                # Not an email format, try standard format
                dataset = DatasetLoader.from_json_file(temp_path)
        elif request.file_format == 'csv':
            dataset = DatasetLoader.from_csv_file(temp_path)
        elif request.file_format == 'yaml':
            dataset = DatasetLoader.from_yaml_file(temp_path)
        elif request.file_format == 'txt':
            dataset = DatasetLoader.from_text_file(temp_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.file_format}")
        
        # Use provided name or dataset name
        dataset_name = request.name or dataset.name
        
        # Check if name already exists
        existing = await dataset_repository.get_by_name(dataset_name)
        if existing:
            raise HTTPException(status_code=400, detail="Dataset with this name already exists")
        
        # Create dataset document
        dataset_doc = DatasetDocument(
            name=dataset_name,
            description=dataset.description,
            questions=[q.to_dict() for q in dataset.questions],
            enabled=True,
            metadata=dataset.metadata
        )
        
        dataset_id = await dataset_repository.create(dataset_doc)
        created_dataset = await dataset_repository.get_by_id(dataset_id)
        
        return dataset_doc_to_response(created_dataset)
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@app.put("/api/datasets/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(dataset_id: str, request: DatasetUpdateRequest):
    """Update a dataset."""
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    success = await dataset_repository.update(dataset_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    updated_dataset = await dataset_repository.get_by_id(dataset_id)
    return dataset_doc_to_response(updated_dataset)


@app.delete("/api/datasets/{dataset_id}", status_code=204)
async def delete_dataset(dataset_id: str):
    """Delete a dataset."""
    success = await dataset_repository.delete(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

