from typing import Dict, Any
from .evaluator import BaseEvaluator
from .metric_base import StandardMetric
from .responses import EvaluatorResponse


class RelevanceMetric(StandardMetric):
    """Metric for evaluating the relevance of a response to a prompt."""

    def __init__(self):
        evaluation_instructions = """Please evaluate the relevance of the response to the prompt on a scale of 0-10, where:
        - 0: Completely irrelevant or off-topic
        - 5: Somewhat relevant but missing key points or going off-topic
        - 10: Perfectly relevant and directly addresses all aspects of the prompt"""
        
        super().__init__(
            name="relevance",
            description="Measures how well the response addresses the prompt's requirements and stays on topic",
            evaluation_instructions=evaluation_instructions
        )

    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator) -> EvaluatorResponse:
        eval_prompt = f"""You are evaluating how relevant a model's response is to the given prompt.

        ### Prompt:
        {prompt}

        ### Response:
        {response}

        Please evaluate the relevance of the response to the prompt on a scale of 0-10, where:
        - 0: Completely irrelevant or off-topic
        - 5: Somewhat relevant but missing key points or going off-topic
        - 10: Perfectly relevant and directly addresses all aspects of the prompt

        Your response must follow this exact format:
        Score: [your score out of 10]

        Rationale: [your explanation of the score, including what aspects were relevant or irrelevant]
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
