from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass, asdict
import json
import logging

# Set up logger for responses
logger = logging.getLogger(__name__)


class ModelResponse(BaseModel):
    """Container for model responses."""
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IndividualResponse(BaseModel):
    """Individual response from a single evaluator model with validation."""
    model_name: str = Field(..., min_length=1, description="Name of the evaluator model")
    score: float = Field(..., ge=0, le=10, description="Score from 0 to 10")
    rationale: str = Field(..., min_length=1, description="Explanation for the score")
    
    @validator('rationale')
    def validate_rationale(cls, v):
        """Ensure rationale is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError('Rationale cannot be empty or just whitespace')
        return v.strip()
    
    @validator('score')
    def validate_score_precision(cls, v):
        """Round score to 1 decimal place for consistency."""
        return round(v, 1)


class EvaluatorResponse(BaseModel):
    """Response from an evaluator model with validation."""
    metric_name: str = Field(..., min_length=1, description="Name of the metric")
    score: float = Field(..., ge=0, le=10, description="Average score across all evaluators")
    rationale: str = Field(..., min_length=1, description="Combined rationale")
    individual_responses: List[IndividualResponse] = Field(..., min_items=1, description="Individual evaluator responses")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('score')
    def validate_score_precision(cls, v):
        """Round score to 1 decimal place for consistency."""
        return round(v, 1)
    
    @validator('rationale')
    def validate_rationale(cls, v):
        """Ensure rationale is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError('Rationale cannot be empty or just whitespace')
        return v.strip()
    
    @validator('individual_responses')
    def validate_individual_responses(cls, v):
        """Ensure there's at least one individual response."""
        if not v:
            raise ValueError('At least one individual response is required')
        return v


@dataclass
class PromptEvaluation:
    """Evaluation results for a single prompt."""
    prompt: str
    response: str
    evaluations: List[EvaluatorResponse]
    metadata: Dict[str, Any] = None  # Optional metadata (e.g., original_query for RAG)
    
    def __post_init__(self):
        """Validate prompt evaluation after initialization."""
        if not self.prompt or not self.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if not self.response or not self.response.strip():
            raise ValueError("Response cannot be empty")
        if not self.evaluations:
            raise ValueError("At least one evaluation is required")
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BenchmarkResult:
    """Results from running a benchmark with enhanced validation and error handling."""
    prompt_evaluations: List[PromptEvaluation]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate benchmark result after initialization."""
        if not self.prompt_evaluations:
            raise ValueError("At least one prompt evaluation is required")
        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")

    @classmethod
    def combine(cls, results: List['BenchmarkResult'], model_name: str) -> 'BenchmarkResult':
        """
        Combine results from multiple metrics into a single benchmark result.
        
        Args:
            results: List of BenchmarkResults from different metrics
            model_name: Name of the model being evaluated
            
        Returns:
            Combined BenchmarkResult
            
        Raises:
            ValueError: If no results provided or results are inconsistent
        """
        if not results:
            raise ValueError("No results to combine")
        
        logger.info(f"Combining {len(results)} benchmark results for model {model_name}")
        
        # Validate that all results have the same prompts
        base_prompts = {pe.prompt for pe in results[0].prompt_evaluations}
        for i, result in enumerate(results[1:], 1):
            result_prompts = {pe.prompt for pe in result.prompt_evaluations}
            if base_prompts != result_prompts:
                logger.warning(f"Result {i} has different prompts than the base result")
        
        # Combine prompt evaluations
        combined_evaluations = []
        for prompt_eval in results[0].prompt_evaluations:
            # Get all evaluations for this prompt from all metrics
            all_evaluations = []
            combined_pe_metadata = dict(prompt_eval.metadata) if prompt_eval.metadata else {}
            
            for result in results:
                matching_eval = next(
                    (e for e in result.prompt_evaluations if e.prompt == prompt_eval.prompt),
                    None
                )
                if matching_eval:
                    all_evaluations.extend(matching_eval.evaluations)
                    # Merge metadata from matching evaluations
                    if matching_eval.metadata:
                        combined_pe_metadata.update(matching_eval.metadata)
                else:
                    logger.warning(f"No matching evaluation found for prompt: {prompt_eval.prompt[:50]}...")
            
            if all_evaluations:  # Only add if we have evaluations
                combined_evaluations.append(PromptEvaluation(
                    prompt=prompt_eval.prompt,
                    response=prompt_eval.response,
                    evaluations=all_evaluations,
                    metadata=combined_pe_metadata
                ))
        
        # Combine metadata
        all_metrics = []
        evaluator_models = []
        
        for result in results:
            if "metrics" in result.metadata:
                all_metrics.extend(result.metadata["metrics"])
            if "evaluator_models" in result.metadata:
                evaluator_models = result.metadata["evaluator_models"]  # Should be same for all
        
        combined_metadata = {
            "model_name": model_name,
            "num_prompts": len(combined_evaluations),
            "num_metrics": len(set(all_metrics)),  # Use set to avoid duplicates
            "metrics": list(set(all_metrics)),  # Remove duplicates
            "evaluator_models": evaluator_models,
            "combined_from": len(results)
        }
        
        # Add any additional metadata from the first result
        for key, value in results[0].metadata.items():
            if key not in combined_metadata:
                combined_metadata[key] = value
        
        logger.info(f"Successfully combined results: {len(combined_evaluations)} prompts, {len(set(all_metrics))} metrics")
        
        return cls(
            prompt_evaluations=combined_evaluations,
            metadata=combined_metadata
        )

    def to_json(self) -> str:
        """
        Export the benchmark result to JSON string with error handling.
        
        Returns:
            JSON string representation of the benchmark result
            
        Raises:
            ValueError: If serialization fails
        """
        try:
            def convert_to_serializable(obj):
                """Recursively convert objects to JSON-serializable format."""
                if hasattr(obj, 'dict'):  # Pydantic model
                    return obj.dict()
                elif hasattr(obj, '__dataclass_fields__'):  # Dataclass
                    result = {}
                    for field_name, field_value in asdict(obj).items():
                        result[field_name] = convert_to_serializable(field_value)
                    return result
                elif isinstance(obj, list):
                    return [convert_to_serializable(item) for item in obj]
                elif isinstance(obj, dict):
                    return {key: convert_to_serializable(value) for key, value in obj.items()}
                else:
                    return obj
            
            # Convert the entire object to a serializable dictionary
            result_dict = convert_to_serializable(self)
            
            # Convert to JSON string with proper formatting
            return json.dumps(result_dict, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Failed to serialize benchmark result to JSON: {e}")
            raise ValueError(f"JSON serialization failed: {e}")

    @classmethod
    def from_json(cls, json_str: str) -> 'BenchmarkResult':
        """
        Create a BenchmarkResult instance from a JSON string with enhanced validation.
        
        Args:
            json_str: JSON string representation of a benchmark result
            
        Returns:
            BenchmarkResult instance
            
        Raises:
            ValueError: If the JSON is invalid or missing required fields
            json.JSONDecodeError: If the JSON string is malformed
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise json.JSONDecodeError(f"Invalid JSON format: {e}", json_str, e.pos)
        
        # Validate required fields
        required_fields = ['prompt_evaluations', 'metadata']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: '{field}'")
        
        if not isinstance(data['prompt_evaluations'], list):
            raise ValueError("'prompt_evaluations' must be a list")
        
        if not isinstance(data['metadata'], dict):
            raise ValueError("'metadata' must be a dictionary")
        
        try:
            # Reconstruct nested objects
            prompt_evaluations = []
            for pe_data in data['prompt_evaluations']:
                evaluations = []
                for eval_data in pe_data['evaluations']:
                    # Reconstruct individual responses with validation
                    individual_responses = []
                    for ir_data in eval_data['individual_responses']:
                        individual_response = IndividualResponse(**ir_data)
                        individual_responses.append(individual_response)
                    
                    # Handle metadata field which might be None
                    metadata = eval_data.get('metadata', {})
                    if metadata is None:
                        metadata = {}
                    
                    # Create EvaluatorResponse with validation
                    evaluation = EvaluatorResponse(
                        metric_name=eval_data['metric_name'],
                        score=eval_data['score'],
                        rationale=eval_data['rationale'],
                        individual_responses=individual_responses,
                        metadata=metadata
                    )
                    evaluations.append(evaluation)
                
                # Create PromptEvaluation with validation
                prompt_evaluation = PromptEvaluation(
                    prompt=pe_data['prompt'],
                    response=pe_data['response'],
                    evaluations=evaluations
                )
                prompt_evaluations.append(prompt_evaluation)
            
            result = cls(
                prompt_evaluations=prompt_evaluations,
                metadata=data['metadata']
            )
            
            logger.info(f"Successfully loaded benchmark result with {len(prompt_evaluations)} prompt evaluations")
            return result
            
        except Exception as e:
            logger.error(f"Failed to reconstruct benchmark result from JSON: {e}")
            raise ValueError(f"Failed to reconstruct benchmark result: {e}")

    def save_to_json_file(self, filepath: str) -> None:
        """
        Save the benchmark result to a JSON file with error handling.
        
        Args:
            filepath: Path where to save the JSON file
            
        Raises:
            IOError: If the file cannot be written
            ValueError: If serialization fails
        """
        try:
            logger.info(f"Saving benchmark result to {filepath}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            logger.info(f"Successfully saved benchmark result to {filepath}")
        except IOError as e:
            logger.error(f"Failed to save benchmark result to {filepath}: {e}")
            raise IOError(f"Failed to save benchmark result to {filepath}: {e}")

    @classmethod 
    def load_from_json_file(cls, filepath: str) -> 'BenchmarkResult':
        """
        Load a BenchmarkResult instance from a JSON file with error handling.
        
        Args:
            filepath: Path to the JSON file to load
            
        Returns:
            BenchmarkResult instance
            
        Raises:
            IOError: If the file cannot be read
            ValueError: If the JSON is invalid or missing required fields
            json.JSONDecodeError: If the JSON string is malformed
        """
        try:
            logger.info(f"Loading benchmark result from {filepath}")
            with open(filepath, 'r', encoding='utf-8') as f:
                json_str = f.read()
            result = cls.from_json(json_str)
            logger.info(f"Successfully loaded benchmark result from {filepath}")
            return result
        except IOError as e:
            logger.error(f"Failed to load benchmark result from {filepath}: {e}")
            raise IOError(f"Failed to load benchmark result from {filepath}: {e}")

    def get_average_scores_by_metric(self) -> Dict[str, float]:
        """
        Get average scores for each metric with improved error handling.
        
        Returns:
            Dictionary mapping metric names to average scores
        """
        metric_scores = {}
        for evaluation in self.prompt_evaluations:
            for eval_result in evaluation.evaluations:
                metric_name = eval_result.metric_name
                if metric_name not in metric_scores:
                    metric_scores[metric_name] = []
                metric_scores[metric_name].append(eval_result.score)
        
        # Calculate averages and round to 1 decimal place
        return {
            metric: round(sum(scores) / len(scores), 1) if scores else 0.0
            for metric, scores in metric_scores.items()
        }

    def get_model_scores_by_metric(self, metric_name: str) -> Dict[str, List[float]]:
        """
        Get all scores for a specific metric, broken down by evaluator model.
        
        Args:
            metric_name: Name of the metric to get scores for
            
        Returns:
            Dictionary mapping evaluator model names to their scores
            
        Raises:
            ValueError: If metric_name is not found
        """
        if not metric_name:
            raise ValueError("Metric name cannot be empty")
        
        model_scores = {}
        found_metric = False
        
        for evaluation in self.prompt_evaluations:
            for eval_result in evaluation.evaluations:
                if eval_result.metric_name == metric_name:
                    found_metric = True
                    for individual in eval_result.individual_responses:
                        model_name = individual.model_name
                        if model_name not in model_scores:
                            model_scores[model_name] = []
                        model_scores[model_name].append(individual.score)
        
        if not found_metric:
            available_metrics = list(self.get_average_scores_by_metric().keys())
            raise ValueError(f"Metric '{metric_name}' not found. Available metrics: {available_metrics}")
        
        return model_scores
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive summary statistics for the benchmark result.
        
        Returns:
            Dictionary containing various statistics
        """
        avg_scores = self.get_average_scores_by_metric()
        
        stats = {
            "num_prompts": len(self.prompt_evaluations),
            "num_metrics": len(avg_scores),
            "metrics": list(avg_scores.keys()),
            "average_scores": avg_scores,
            "overall_average": round(sum(avg_scores.values()) / len(avg_scores), 1) if avg_scores else 0.0,
            "model_name": self.metadata.get("model_name", "Unknown"),
            "evaluator_models": self.metadata.get("evaluator_models", [])
        }
        
        # Add score distribution
        all_scores = []
        for evaluation in self.prompt_evaluations:
            for eval_result in evaluation.evaluations:
                all_scores.append(eval_result.score)
        
        if all_scores:
            stats["score_distribution"] = {
                "min": min(all_scores),
                "max": max(all_scores),
                "median": sorted(all_scores)[len(all_scores) // 2],
                "std_dev": round((sum((x - stats["overall_average"]) ** 2 for x in all_scores) / len(all_scores)) ** 0.5, 2)
            }
        
        return stats


class MetricResult(BaseModel):
    """Container for metric evaluation results with validation."""
    score: float = Field(..., ge=0, le=10, description="Score from 0 to 10")
    rationale: Optional[str] = Field(None, description="Optional explanation")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('score')
    def validate_score_precision(cls, v):
        """Round score to 1 decimal place for consistency."""
        return round(v, 1) 