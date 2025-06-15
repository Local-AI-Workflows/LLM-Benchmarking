from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any, Optional
import re

from models.base_model import BaseLLMModel
from .responses import EvaluatorResponse


class BaseEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, evaluation: str, metric_name: str, metric_description: str) -> EvaluatorResponse:
        raise NotImplementedError()


class _SingleEvaluator(BaseEvaluator):
    def __init__(self, model: BaseLLMModel):
        self.model = model

    async def evaluate(self, evaluation: str, metric_name: str, metric_description: str) -> EvaluatorResponse:
        raw = await self.model.generate(evaluation)
        score = float(raw.text.split()[0])
        rationale = " ".join(raw.text.split()[1:])
        
        return EvaluatorResponse(
            metric_name=metric_name,
            metric_description=metric_description,
            average_score=score,
            individual_responses=[{
                "score": score,
                "rationale": rationale,
                "model_name": self.model.model_name
            }],
            metadata=raw.metadata
        )


class BaseEvaluator:
    """Base class for evaluators."""
    
    def __init__(self, model: BaseLLMModel):
        self.model = model
    
    async def evaluate(
        self,
        evaluation: str,
        metric_name: str,
        metric_description: str
    ) -> EvaluatorResponse:
        """
        Evaluate a response using the evaluator model.
        
        Args:
            evaluation: The evaluation prompt
            metric_name: Name of the metric being evaluated
            metric_description: Description of the metric
            
        Returns:
            EvaluatorResponse containing the evaluation results
        """
        response = await self.model.generate(evaluation)
        
        # Filter out think blocks if present
        text = response.text
        think_pattern = r'<think>.*?</think>'
        text = re.sub(think_pattern, '', text, flags=re.DOTALL)
        
        # Parse score and rationale
        score = self._extract_score(text)
        rationale = self._extract_rationale(text)
        
        return EvaluatorResponse(
            metric_name=metric_name,
            score=score,
            rationale=rationale,
            metadata={
                "model_name": self.model.model_name,
                "metric_description": metric_description
            }
        )
    
    def _extract_score(self, text: str) -> float:
        """Extract the score from the evaluator's response."""
        # Look for score in format "Score: X" or "Score: X/10"
        score_match = re.search(r'Score:\s*(\d+(?:\.\d+)?)', text)
        if score_match:
            return float(score_match.group(1))
        
        # Look for score in format "X/10"
        score_match = re.search(r'(\d+(?:\.\d+)?)/10', text)
        if score_match:
            return float(score_match.group(1))
        
        # Look for score in format "X out of 10"
        score_match = re.search(r'(\d+(?:\.\d+)?)\s*out of\s*10', text)
        if score_match:
            return float(score_match.group(1))
        
        # Default to 0 if no score found
        return 0.0
    
    def _extract_rationale(self, text: str) -> str:
        """Extract the rationale from the evaluator's response."""
        # Look for rationale after "Rationale:" or "Explanation:"
        rationale_match = re.search(r'(?:Rationale|Explanation):\s*(.*?)(?:\n\n|\Z)', text, re.DOTALL)
        if rationale_match:
            return rationale_match.group(1).strip()
        
        # If no clear rationale section, return the whole text
        return text.strip()


class _MultiEvaluator(BaseEvaluator):
    """Evaluator that uses multiple models and averages their scores."""
    
    def __init__(self, models: List[BaseLLMModel]):
        """
        Initialize the multi-evaluator.
        
        Args:
            models: List of models to use for evaluation
        """
        super().__init__(models[0])  # Use first model as base
        self.models = models
    
    async def evaluate(
        self,
        evaluation: str,
        metric_name: str,
        metric_description: str
    ) -> EvaluatorResponse:
        """
        Evaluate using multiple models and average their scores.
        
        Args:
            evaluation: The evaluation prompt
            metric_name: Name of the metric being evaluated
            metric_description: Description of the metric
            
        Returns:
            EvaluatorResponse containing the averaged evaluation results
        """
        total_score = 0.0
        individual_responses = []
        
        for model in self.models:
            response = await model.generate(evaluation)
            
            # Filter out think blocks if present
            text = response.text
            think_pattern = r'<think>.*?</think>'
            text = re.sub(think_pattern, '', text, flags=re.DOTALL)
            
            # Parse score and rationale
            score = self._extract_score(text)
            rationale = self._extract_rationale(text)
            
            total_score += score
            individual_responses.append({
                "score": score,
                "rationale": rationale,
                "model_name": model.model_name
            })
        
        average_score = total_score / len(self.models) if self.models else 0.0
        
        # Combine rationales from all models
        combined_rationale = "\n\n".join([
            f"Evaluation from {resp['model_name']}:\n{resp['rationale']}"
            for resp in individual_responses
        ])
        
        return EvaluatorResponse(
            metric_name=metric_name,
            score=average_score,
            rationale=combined_rationale,
            metadata={
                "model_name": "multi-evaluator",
                "metric_description": metric_description,
                "individual_responses": individual_responses
            }
        )


class EvaluatorFactory:
    @staticmethod
    def create_evaluator(models: Union[BaseLLMModel, List[BaseLLMModel]]) -> BaseEvaluator:
        if isinstance(models, list):
            return _MultiEvaluator(models)
        elif isinstance(models, BaseLLMModel):
            return _SingleEvaluator(models)
        raise ValueError("Invalid model type. Must be BaseLLMModel or List[BaseLLMModel].")
