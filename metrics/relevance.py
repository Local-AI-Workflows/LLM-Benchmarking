from typing import Dict, Any
from .metric_base import BaseMetric, MetricResult
from models.ollama_model import OllamaModel

class RelevanceMetric(BaseMetric):
    """Evaluates how relevant a response is to the given prompt."""
    
    def __init__(self):
        super().__init__(
            name="relevance",
            description="Measures how well the response addresses the prompt's intent"
        )
    
    async def evaluate(self, prompt: str, response: str, **kwargs) -> MetricResult:
        """
        Evaluate the relevance of a response to its prompt using an LLM evaluator.
        
        Args:
            prompt: The input prompt
            response: The model's response
            **kwargs: Additional arguments (e.g., evaluator_model)
            
        Returns:
            MetricResult with relevance score and rationale
        """
        evaluator_model = kwargs.get('evaluator_model')
        if not evaluator_model:
            raise ValueError("evaluator_model is required for evaluation")
        
        # Create evaluation prompt
        eval_prompt = f"""Evaluate how relevant the following response is to the given prompt.

Prompt: {prompt}

Response: {response}

Rate the relevance on a scale of 1-5, where:
1: Completely irrelevant
2: Mostly irrelevant
3: Somewhat relevant
4: Mostly relevant
5: Completely relevant

Provide your rating as a single number (1-5) followed by a brief explanation.

Your evaluation:"""

        # Get evaluation from the model
        eval_response = await evaluator_model.generate(eval_prompt)
        
        # Parse the response to extract score and rationale
        try:
            # Extract the first number from the response
            score = float(eval_response.text.split()[0])
            # Get the rest as rationale
            rationale = " ".join(eval_response.text.split()[1:])
        except (ValueError, IndexError):
            score = 0.0
            rationale = "Failed to parse evaluation response"
        
        return MetricResult(
            score=score,
            rationale=rationale,
            metadata={
                "evaluation_method": "ollama_llm",
                "evaluator_model": evaluator_model.model_name,
                "prompt_length": len(prompt),
                "response_length": len(response)
            }
        ) 