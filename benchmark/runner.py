from typing import List, Dict, Any
from models.base_model import BaseLLMModel
from metrics.evaluator import BaseEvaluator
from metrics.metric_base import BaseMetric
from metrics.responses import BenchmarkResult


class BenchmarkRunner:
    """Runs benchmarks across multiple prompts and metrics."""

    def __init__(self, evaluator: BaseEvaluator, metrics: List[BaseMetric]):
        """
        Initialize the benchmark runner.
        
        Args:
            evaluator: The evaluator to use for assessing responses
            metrics: List of metrics to use for evaluation
        """
        self.evaluator = evaluator
        self.metrics = metrics

    async def run_benchmark(
        self, 
        model: BaseLLMModel,
        prompts: List[str]
    ) -> BenchmarkResult:
        """
        Run the benchmark for a specific model across multiple prompts.
        
        Args:
            model: The model to evaluate
            prompts: List of prompts to evaluate the model on
            
        Returns:
            BenchmarkResult containing all evaluation results
        """
        # Get responses from the model
        model_responses = {}
        for prompt in prompts:
            response = await model.generate(prompt)
            model_responses[prompt] = response.text
        
        # Run each metric
        results = []
        for metric in self.metrics:
            result = await metric.evaluate_batch(prompts, model_responses, self.evaluator)
            results.append(result)
        
        # Combine results from all metrics
        return BenchmarkResult.combine(results, model.model_name) 