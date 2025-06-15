from .evaluator import BaseEvaluator
from .metric_base import BaseMetric, MetricResult


class RelevanceMetric(BaseMetric):
    """Evaluates how relevant a response is to the given prompt."""

    def __init__(self):
        super().__init__(
            name="relevance",
            description="Measures how well the response addresses the prompt's intent"
        )

    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator) -> MetricResult:
        eval_prompt = f"""You are evaluating how relevant a model's response is to the given prompt.

        ### Prompt:
        {prompt}

        ### Response:
        {response}

        ### Scoring Instructions:
        Rate the relevance of the response on a scale from **1 to 5**, where:

        1 = Not relevant at all  
        2 = Slightly relevant  
        3 = Moderately relevant  
        4 = Very relevant  
        5 = Extremely relevant

        ### Format:
        Please respond with your score as **a single digit followed by a space**, then **a short sentence justifying your rating**.

        ### Example Response:
        5 The response directly and fully answers the question.

        ### Now, your evaluation:
        """
        eval_response = await evaluator.evaluate(eval_prompt)

        return MetricResult(
            score=eval_response.average_score(),
            rationale=eval_response.combined_rationale(),
            metadata={
                "evaluation_method": "ollama_llm",
                "num_evaluators": len(eval_response.results),
                **eval_response.metadata,
                "prompt_length": len(prompt),
                "response_length": len(response)
            }
        )
