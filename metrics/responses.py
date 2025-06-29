from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from dataclasses import dataclass, asdict
import json


class ModelResponse(BaseModel):
    """Container for model responses."""
    text: str
    metadata: Dict[str, Any]


@dataclass
class IndividualResponse:
    """Individual response from a single evaluator model."""
    model_name: str
    score: float
    rationale: str


@dataclass
class EvaluatorResponse:
    """Response from an evaluator model."""
    metric_name: str
    score: float  # Average score across all evaluators
    rationale: str
    individual_responses: List[IndividualResponse]
    metadata: Dict[str, Any] = None


@dataclass
class PromptEvaluation:
    """Evaluation results for a single prompt."""
    prompt: str
    response: str
    evaluations: List[EvaluatorResponse]


@dataclass
class BenchmarkResult:
    """Results from running a benchmark."""
    prompt_evaluations: List[PromptEvaluation]
    metadata: Dict[str, Any]

    @classmethod
    def combine(cls, results: List['BenchmarkResult'], model_name: str) -> 'BenchmarkResult':
        """
        Combine results from multiple metrics into a single benchmark result.
        
        Args:
            results: List of BenchmarkResults from different metrics
            model_name: Name of the model being evaluated
            
        Returns:
            Combined BenchmarkResult
        """
        if not results:
            raise ValueError("No results to combine")
        
        # Combine prompt evaluations
        combined_evaluations = []
        for prompt_eval in results[0].prompt_evaluations:
            # Get all evaluations for this prompt from all metrics
            all_evaluations = []
            for result in results:
                matching_eval = next(
                    (e for e in result.prompt_evaluations if e.prompt == prompt_eval.prompt),
                    None
                )
                if matching_eval:
                    all_evaluations.extend(matching_eval.evaluations)
            
            combined_evaluations.append(PromptEvaluation(
                prompt=prompt_eval.prompt,
                response=prompt_eval.response,
                evaluations=all_evaluations
            ))
        
        # Combine metadata
        combined_metadata = {
            "model_name": model_name,
            "num_prompts": len(combined_evaluations),
            "num_metrics": len(results),
            "metrics": [metric for result in results for metric in result.metadata["metrics"]],
            "evaluator_models": results[0].metadata["evaluator_models"]  # All results should have same evaluators
        }
        
        return cls(
            prompt_evaluations=combined_evaluations,
            metadata=combined_metadata
        )

    def to_json(self) -> str:
        """
        Export the benchmark result to JSON string.
        
        Returns:
            JSON string representation of the benchmark result
        """
        def convert_to_dict(obj):
            """Convert dataclass objects to dictionaries."""
            if hasattr(obj, '__dataclass_fields__'):
                return asdict(obj)
            return obj
        
        # Convert the entire object to a dictionary
        result_dict = asdict(self)
        
        # Convert to JSON string with proper formatting
        return json.dumps(result_dict, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'BenchmarkResult':
        """
        Create a BenchmarkResult instance from a JSON string.
        
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
            raise json.JSONDecodeError(f"Invalid JSON format: {e}")
        
        # Validate required fields
        if 'prompt_evaluations' not in data:
            raise ValueError("Missing required field: 'prompt_evaluations'")
        if 'metadata' not in data:
            raise ValueError("Missing required field: 'metadata'")
        
        # Reconstruct nested objects
        prompt_evaluations = []
        for pe_data in data['prompt_evaluations']:
            evaluations = []
            for eval_data in pe_data['evaluations']:
                individual_responses = [
                    IndividualResponse(**ir_data) 
                    for ir_data in eval_data['individual_responses']
                ]
                
                # Handle metadata field which might be None
                metadata = eval_data.get('metadata')
                if metadata is None:
                    metadata = {}
                
                evaluation = EvaluatorResponse(
                    metric_name=eval_data['metric_name'],
                    score=eval_data['score'],
                    rationale=eval_data['rationale'],
                    individual_responses=individual_responses,
                    metadata=metadata
                )
                evaluations.append(evaluation)
            
            prompt_evaluation = PromptEvaluation(
                prompt=pe_data['prompt'],
                response=pe_data['response'],
                evaluations=evaluations
            )
            prompt_evaluations.append(prompt_evaluation)
        
        return cls(
            prompt_evaluations=prompt_evaluations,
            metadata=data['metadata']
        )

    def save_to_json_file(self, filepath: str) -> None:
        """
        Save the benchmark result to a JSON file.
        
        Args:
            filepath: Path where to save the JSON file
            
        Raises:
            IOError: If the file cannot be written
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
        except IOError as e:
            raise IOError(f"Failed to save benchmark result to {filepath}: {e}")

    @classmethod 
    def load_from_json_file(cls, filepath: str) -> 'BenchmarkResult':
        """
        Load a BenchmarkResult instance from a JSON file.
        
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
            with open(filepath, 'r', encoding='utf-8') as f:
                json_str = f.read()
            return cls.from_json(json_str)
        except IOError as e:
            raise IOError(f"Failed to load benchmark result from {filepath}: {e}")

    def get_average_scores_by_metric(self) -> Dict[str, float]:
        """Get average scores for each metric."""
        metric_scores = {}
        for evaluation in self.prompt_evaluations:
            for eval_result in evaluation.evaluations:
                if eval_result.metric_name not in metric_scores:
                    metric_scores[eval_result.metric_name] = []
                metric_scores[eval_result.metric_name].append(eval_result.score)
        
        return {
            metric: sum(scores) / len(scores)
            for metric, scores in metric_scores.items()
        }

    def get_model_scores_by_metric(self, metric_name: str) -> Dict[str, List[float]]:
        """
        Get all scores for a specific metric, broken down by evaluator model.
        
        Args:
            metric_name: Name of the metric to get scores for
            
        Returns:
            Dictionary mapping evaluator model names to their scores
        """
        model_scores = {}
        for evaluation in self.prompt_evaluations:
            for eval_result in evaluation.evaluations:
                if eval_result.metric_name == metric_name:
                    for individual in eval_result.individual_responses:
                        if individual.model_name not in model_scores:
                            model_scores[individual.model_name] = []
                        model_scores[individual.model_name].append(individual.score)
        return model_scores


class MetricResult(BaseModel):
    """Container for metric evaluation results."""
    score: float
    rationale: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None 