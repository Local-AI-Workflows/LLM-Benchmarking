from abc import ABC, abstractmethod
from typing import List, Dict, Any

from .evaluator import BaseEvaluator
from .responses import EvaluatorResponse, BenchmarkResult, PromptEvaluation


class BaseMetric(ABC):
    """Base class for all metrics in the benchmarking system."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize the metric.
        
        Args:
            name: Name of the metric
            description: Description of what the metric measures
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator) -> EvaluatorResponse:
        """
        Evaluate a single response.
        
        Args:
            prompt: The input prompt
            response: The model's response
            evaluator: The evaluator to use
            
        Returns:
            EvaluatorResponse containing the evaluation results
        """
        pass

    async def evaluate_batch(
        self, 
        prompts: List[str], 
        responses: Dict[str, str], 
        evaluator: BaseEvaluator
    ) -> BenchmarkResult:
        """
        Evaluate a batch of responses.
        
        Args:
            prompts: List of prompts
            responses: Dictionary mapping prompts to responses
            evaluator: The evaluator to use
            
        Returns:
            BenchmarkResult containing all evaluations
        """
        prompt_evaluations = []
        
        for prompt in prompts:
            response = responses[prompt]
            evaluation = await self.evaluate(prompt, response, evaluator)
            
            prompt_evaluations.append(PromptEvaluation(
                prompt=prompt,
                response=response,
                evaluations=[evaluation]
            ))
        
        # Get evaluator model names
        evaluator_models = []
        if hasattr(evaluator, 'models'):
            evaluator_models = [model.model_name for model in evaluator.models]
        elif hasattr(evaluator, 'model_name'):
            evaluator_models = [evaluator.model_name]
        
        return BenchmarkResult(
            prompt_evaluations=prompt_evaluations,
            metadata={
                "num_prompts": len(prompts),
                "num_metrics": 1,
                "metrics": [self.name],
                "evaluator_models": evaluator_models
            }
        )
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


class StandardMetric(BaseMetric):
    """Base class for standard metrics that follow a common evaluation pattern."""
    
    def __init__(self, name: str, description: str, evaluation_instructions: str):
        """
        Initialize the metric.
        
        Args:
            name: Name of the metric
            description: Description of what the metric measures
            evaluation_instructions: Instructions for the evaluator model
        """
        super().__init__(name, description)
        self.evaluation_instructions = evaluation_instructions
    
    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator) -> EvaluatorResponse:
        """
        Evaluate a response using the standard evaluation pattern.
        
        Args:
            prompt: The input prompt
            response: The model's response
            evaluator: The evaluator to use
            
        Returns:
            EvaluatorResponse containing the evaluation results
        """
        eval_prompt = f"""You are evaluating {self.name} in a model's response.

        ### Prompt:
        {prompt}

        ### Response:
        {response}

        {self.evaluation_instructions}

        Your response must follow this exact format:
        Score: [your score out of 10]

        Rationale: [your explanation of the score, including specific examples]
        """
        eval_response = await evaluator.evaluate(
            evaluation=eval_prompt,
            metric_name=self.name,
            metric_description=self.description
        )

        # Add standard metadata
        eval_response.metadata.update({
            "prompt_length": len(prompt),
            "response_length": len(response)
        })

        return eval_response 