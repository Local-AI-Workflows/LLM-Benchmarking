from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ModelResponse(BaseModel):
    """Container for model responses."""
    text: str
    metadata: Dict[str, Any]


class EvaluatorResponse(BaseModel):
    """Container for evaluator responses."""
    metric_name: str
    metric_description: str
    average_score: float
    individual_responses: List[Dict[str, Any]]  # list of {"score": float, "rationale": str, "model_name": str}
    metadata: Dict[str, Any] = {}


class PromptEvaluation(BaseModel):
    """Container for evaluation results of a single prompt."""
    prompt: str
    response: str
    evaluations: List[EvaluatorResponse]  # List of evaluations from different metrics


class BenchmarkResult(BaseModel):
    """Container for complete benchmark results."""
    prompt_evaluations: List[PromptEvaluation]
    metadata: Dict[str, Any] = {}

    def get_average_scores_by_metric(self) -> Dict[str, float]:
        """Calculate average scores for each metric across all prompts."""
        metric_scores = {}
        for prompt_eval in self.prompt_evaluations:
            for evaluation in prompt_eval.evaluations:
                metric_name = evaluation.metric_name
                if metric_name not in metric_scores:
                    metric_scores[metric_name] = []
                metric_scores[metric_name].append(evaluation.average_score)
        
        return {
            metric: sum(scores) / len(scores)
            for metric, scores in metric_scores.items()
        }

    def get_model_scores_by_metric(self) -> Dict[str, Dict[str, List[float]]]:
        """Get scores for each model by metric across all prompts."""
        model_scores = {}
        for prompt_eval in self.prompt_evaluations:
            for evaluation in prompt_eval.evaluations:
                metric_name = evaluation.metric_name
                for individual_response in evaluation.individual_responses:
                    model_name = individual_response["model_name"]
                    if model_name not in model_scores:
                        model_scores[model_name] = {}
                    if metric_name not in model_scores[model_name]:
                        model_scores[model_name][metric_name] = []
                    model_scores[model_name][metric_name].append(individual_response["score"])
        
        return model_scores


class MetricResult(BaseModel):
    """Container for metric evaluation results."""
    score: float
    rationale: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None 