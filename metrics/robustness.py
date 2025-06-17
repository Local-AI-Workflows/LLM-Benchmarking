from typing import Dict, Any
from .evaluator import BaseEvaluator
from .metric_base import StandardMetric
from .responses import EvaluatorResponse


class RobustnessMetric(StandardMetric):
    """Metric for evaluating the robustness of a response."""

    def __init__(self):
        evaluation_instructions = """Please evaluate the robustness of the response on a scale of 0-10, where:
        - 0: Response fails to handle ambiguity or edge cases, shows inconsistency
        - 5: Response handles some edge cases but could be more robust
        - 10: Response handles ambiguity and edge cases well, shows consistent behavior"""
        
        super().__init__(
            name="robustness",
            description="Measures how well the response handles edge cases, ambiguity, and potential adversarial inputs",
            evaluation_instructions=evaluation_instructions
        )

    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator) -> EvaluatorResponse:
        eval_prompt = f"""You are evaluating the robustness of a model's response.

        ### Prompt:
        {prompt}

        ### Response:
        {response}

        Please evaluate the robustness of the response on a scale of 0-10, where:
        - 0: Response fails to handle ambiguity or edge cases, shows inconsistency
        - 5: Response handles some edge cases but could be more robust
        - 10: Response handles ambiguity and edge cases well, shows consistent behavior

        Your response must follow this exact format:
        Score: [your score out of 10]

        Rationale: [your explanation of the score, including specific examples of robust or non-robust behavior]
        """
        eval_response = await evaluator.evaluate(
            evaluation=eval_prompt,
            metric_name=self.name,
            metric_description=self.description
        )

        # Add additional metadata
        eval_response.metadata.update({
            "prompt_length": len(prompt),
            "response_length": len(response)
        })

        return eval_response 