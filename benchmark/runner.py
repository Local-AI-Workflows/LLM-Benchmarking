from typing import List, Dict, Any
from models.base_model import BaseLLMModel
from metrics.evaluator import BaseEvaluator, EvaluatorFactory
from metrics.metric_base import BaseMetric
from metrics.responses import BenchmarkResult, PromptEvaluation
from models.ollama_model import OllamaConfig, OllamaModel


class BenchmarkRunner:
    """Runs benchmarks across multiple prompts and metrics."""

    def __init__(self, metrics: List[BaseMetric]):
        """
        Initialize the benchmark runner.
        
        Args:
            metrics: List of metrics to use for evaluation
        """
        # Create evaluator models
        evaluator_models = [
            OllamaModel(config=OllamaConfig(model_name="deepseek-r1:1.5b")),
            OllamaModel(config=OllamaConfig(model_name="gemma3:1b")),
            OllamaModel(config=OllamaConfig(model_name="llama3.2:latest"))
        ]
        self.evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
        self.metrics = metrics

    async def run_benchmark(self, prompts: List[str], model_responses: Dict[str, str]) -> BenchmarkResult:
        """
        Run the benchmark across all prompts and metrics.
        
        Args:
            prompts: List of prompts to evaluate
            model_responses: Dictionary mapping prompts to model responses
            
        Returns:
            BenchmarkResult containing all evaluation results
        """
        prompt_evaluations = []
        
        for prompt in prompts:
            response = model_responses[prompt]
            evaluations = []
            
            # Run each metric
            for metric in self.metrics:
                evaluation = await metric.evaluate(prompt, response, self.evaluator)
                evaluations.append(evaluation)
            
            prompt_evaluations.append(PromptEvaluation(
                prompt=prompt,
                response=response,
                evaluations=evaluations
            ))
        
        return BenchmarkResult(
            prompt_evaluations=prompt_evaluations,
            metadata={
                "num_prompts": len(prompts),
                "num_metrics": len(self.metrics),
                "metrics": [metric.name for metric in self.metrics],
                "evaluator_models": ["deepseek-r1:1.5b", "gemma3:1b", "llama3.2:latest"]
            }
        ) 