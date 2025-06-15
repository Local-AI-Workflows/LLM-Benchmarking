from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any

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


class _MultiEvaluator(BaseEvaluator):
    def __init__(self, models: List[BaseLLMModel]):
        self.models = models

    async def evaluate(self, evaluation: str, metric_name: str, metric_description: str) -> EvaluatorResponse:
        individual_responses = []
        total_score = 0.0
        
        for model in self.models:
            raw = await model.generate(evaluation)
            print(f"Raw response from {model.model_name} :", raw.text)
            try:
                score = float(raw.text.split()[0])
                rationale = " ".join(raw.text.split()[1:])
            except (ValueError, IndexError):
                score = 0.0
                rationale = "Failed to parse: " + raw.text

            individual_responses.append({
                "score": score,
                "rationale": rationale,
                "model_name": model.model_name
            })
            total_score += score

        average_score = total_score / len(self.models) if self.models else 0.0
        
        return EvaluatorResponse(
            metric_name=metric_name,
            metric_description=metric_description,
            average_score=average_score,
            individual_responses=individual_responses,
            metadata={}
        )


class EvaluatorFactory:
    @staticmethod
    def create_evaluator(models: Union[BaseLLMModel, List[BaseLLMModel]]) -> BaseEvaluator:
        if isinstance(models, list):
            return _MultiEvaluator(models)
        elif isinstance(models, BaseLLMModel):
            return _SingleEvaluator(models)
        raise ValueError("Invalid model type. Must be BaseLLMModel or List[BaseLLMModel].")
