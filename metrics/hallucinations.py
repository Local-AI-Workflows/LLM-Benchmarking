from typing import Dict, Any
from .evaluator import BaseEvaluator
from .metric_base import StandardMetric
from .responses import EvaluatorResponse


class HallucinationsMetric(StandardMetric):
    """Metric for evaluating the presence of hallucinations in a response."""

    def __init__(self):
        evaluation_instructions = """Please evaluate the presence of hallucinations in the response on a scale of 0-10, where:
        - 0: Response contains many clear hallucinations or completely fabricated information
        - 5: Response contains some potential hallucinations or uncertain information
        - 10: Response contains no hallucinations and all information appears to be accurate"""
        
        super().__init__(
            name="hallucinations",
            description="Measures the extent to which the response contains fabricated or incorrect information",
            evaluation_instructions=evaluation_instructions
        )

    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator) -> EvaluatorResponse:
        eval_prompt = f"""You are evaluating whether a model's response contains hallucinations (fabricated or incorrect information).

        ### Prompt:
        {prompt}

        ### Response:
        {response}

        Please evaluate the presence of hallucinations in the response on a scale of 0-10, where:
        - 0: Response contains many clear hallucinations or completely fabricated information
        - 5: Response contains some potential hallucinations or uncertain information
        - 10: Response contains no hallucinations and all information appears to be accurate

        Your response must follow this exact format:
        Score: [your score out of 10]

        Rationale: [your explanation of the score, including specific examples of any hallucinations found]
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