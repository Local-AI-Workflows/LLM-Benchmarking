from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any

from pydantic import BaseModel

class BaseEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, evaluation: str) -> "EvaluatorResponse":
        raise NotImplementedError()


class EvaluatorResponse:
    def __init__(self):
        self.individual_responses: List[Dict[str, Any]] = []  # list of {"score": float, "rationale": str, "model_name": str}
        self.metadata: Dict[str, Any] = {}
        self.average_score: float = 0.0

    def add_result(self, score: float, rationale: str = None, model_name: str = None):
        self.individual_responses.append({
            "score": score,
            "rationale": rationale,
            "model_name": model_name
        })
        self._update_average_score()

    def _update_average_score(self):
        if not self.individual_responses:
            self.average_score = 0.0
            return
        self.average_score = sum(r["score"] for r in self.individual_responses) / len(self.individual_responses)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "average_score": self.average_score,
            "individual_responses": self.individual_responses,
            "metadata": self.metadata
        }


class _SingleEvaluator(BaseEvaluator):
    def __init__(self, model: BaseModel):
        self.model = model

    async def evaluate(self, evaluation: str) -> EvaluatorResponse:
        raw = await self.model.generate(evaluation)
        score = float(raw.text.split()[0])
        rationale = " ".join(raw.text.split()[1:])
        response = EvaluatorResponse()
        response.add_result(score, rationale, model_name=self.model.model_name)
        response.metadata = raw.metadata
        return response


class _MultiEvaluator(BaseEvaluator):
    def __init__(self, models: List[BaseModel]):
        self.models = models

    async def evaluate(self, evaluation: str) -> EvaluatorResponse:
        response = EvaluatorResponse()
        for model in self.models:
            raw = await model.generate(evaluation)
            print(f"Raw response from {model.model_name} :", raw.text)
            try:
                score = float(raw.text.split()[0])
                rationale = " ".join(raw.text.split()[1:])
            except (ValueError, IndexError):
                score = 0.0
                rationale = "Failed to parse: " + raw.text

            response.add_result(score, rationale, model_name=model.model_name)
        return response

class EvaluatorFactory:
    @staticmethod
    def create_evaluator(models: Union[BaseModel, List[BaseModel]]) -> BaseEvaluator:
        if isinstance(models, list):
            return _MultiEvaluator(models)
        elif isinstance(models, BaseModel):
            return _SingleEvaluator(models)
        raise ValueError("Invalid model type. Must be BaseModel or List[BaseModel].")
