"""
RAG (Retrieval-Augmented Generation) evaluation metrics.

This module provides metrics for evaluating RAG system responses:
- Faithfulness: Does the response stay true to the retrieved context?
- Relevance: Does the response answer the user's question?
- Language Quality: Is the response well-written and professional?
- Grammatical Correctness: Is the response grammatically correct and easy to understand?
"""

import logging
from typing import Dict, Any, Optional, List
from .metric_base import BaseMetric
from .evaluator import BaseEvaluator
from .responses import EvaluatorResponse, IndividualResponse, BenchmarkResult, PromptEvaluation

logger = logging.getLogger(__name__)


class RAGMetricBase(BaseMetric):
    """
    Base class for RAG evaluation metrics.
    
    RAG metrics evaluate responses in the context of:
    - The original user query
    - The retrieved context used for generation
    - The generated response
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        evaluation_instructions: str,
        scale_min: int = 1,
        scale_max: int = 5
    ):
        """
        Initialize RAG metric.
        
        Args:
            name: Metric name
            description: Metric description
            evaluation_instructions: Instructions for LLM evaluator
            scale_min: Minimum score (default: 1)
            scale_max: Maximum score (default: 5)
        """
        super().__init__(name, description)
        self.evaluation_instructions = evaluation_instructions
        self.scale_min = scale_min
        self.scale_max = scale_max
    
    def _build_evaluation_prompt(
        self,
        query: str,
        context: str,
        response: str
    ) -> str:
        """
        Build the evaluation prompt for the LLM evaluator.
        
        Args:
            query: Original user query
            context: Retrieved context
            response: Generated response
            
        Returns:
            Evaluation prompt string
        """
        return f"""TASK: You are an EVALUATOR, not an assistant. Your job is to RATE the quality of a generated response.

DO NOT answer the user query. DO NOT provide your own response. ONLY evaluate the response below.

## EVALUATION CRITERIA:
{self.evaluation_instructions}

## SCALE: {self.scale_min} (worst) to {self.scale_max} (best)

---

USER QUERY (do NOT answer this, only use it to evaluate):
{query}

RETRIEVED CONTEXT (reference information):
{context}

GENERATED RESPONSE (THIS is what you must evaluate):
{response}

---

IMPORTANT: Output ONLY in this exact format:
Score: [single number from {self.scale_min} to {self.scale_max}]
Rationale: [1-2 sentences explaining your score]

Your evaluation:"""

    async def evaluate(
        self,
        prompt: str,
        response: str,
        evaluator: BaseEvaluator,
        response_obj: Optional[Any] = None
    ) -> EvaluatorResponse:
        """
        Evaluate a RAG response.
        
        Args:
            prompt: The input prompt (query)
            response: The model's response
            evaluator: The evaluator to use
            response_obj: Optional response object containing metadata (context, tool calls, etc.)
            
        Returns:
            EvaluatorResponse containing the evaluation results
        """
        # Extract context from response object metadata
        context = ""
        if response_obj and hasattr(response_obj, 'metadata'):
            metadata = response_obj.metadata
            # Try different keys where context might be stored
            context = metadata.get('retrieved_context', '')
            if not context:
                context = metadata.get('context', '')
            if not context:
                # Try to extract from tool results
                tool_results = metadata.get('tool_results', [])
                if tool_results:
                    context = "\n\n".join([
                        str(result.get('result', '')) 
                        for result in tool_results 
                        if result.get('result')
                    ])
            if not context:
                context = metadata.get('reference_context', '')
        
        if not context:
            logger.warning(f"No context found for RAG evaluation of metric {self.name}")
            context = "[No context retrieved]"
        
        # Build evaluation prompt
        evaluation_prompt = self._build_evaluation_prompt(prompt, context, response)
        
        # Use evaluator to get score and rationale
        try:
            result = await evaluator.evaluate(
                evaluation_prompt,
                metric_name=self.name,
                metric_description=self.description
            )
            return result
        except Exception as e:
            logger.error(f"Error evaluating {self.name}: {e}")
            return EvaluatorResponse(
                metric_name=self.name,
                score=0.0,
                rationale=f"Evaluation failed: {str(e)}",
                individual_responses=[IndividualResponse(
                    model_name="error",
                    score=0.0,
                    rationale=f"Evaluation failed: {str(e)}"
                )],
                metadata={"error": str(e)}
            )


class FaithfulnessMetric(RAGMetricBase):
    """
    Measures whether the response is faithful to the retrieved context.
    
    A faithful response:
    - Only uses information from the provided context
    - Does not hallucinate facts not in the context
    - Correctly attributes information
    """
    
    def __init__(self):
        super().__init__(
            name="faithfulness",
            description="Measures if the response stays true to the retrieved context without hallucination",
            evaluation_instructions="""
Evaluate the FAITHFULNESS of the response. Faithfulness measures whether the response:
- Only uses information from the provided context
- Does NOT hallucinate or make up facts not present in the context
- Correctly represents information from the context without distortion

Scoring guide:
- 5: Completely faithful - all claims are supported by the context
- 4: Mostly faithful - minor unsupported claims that don't affect accuracy
- 3: Partially faithful - some unsupported claims but core information is correct
- 2: Mostly unfaithful - significant unsupported or contradicting claims
- 1: Completely unfaithful - response contradicts context or is entirely fabricated
"""
        )


class RelevanceMetric(RAGMetricBase):
    """
    Measures whether the response actually answers the user's question.
    
    A relevant response:
    - Directly addresses the user's query
    - Provides useful and pertinent information
    - Stays on topic
    """
    
    def __init__(self):
        super().__init__(
            name="relevance",
            description="Measures if the response directly answers the user's question",
            evaluation_instructions="""
Evaluate the RELEVANCE of the response. Relevance measures whether the response:
- Directly addresses the user's query
- Provides information that is useful for answering the question
- Stays on topic without unnecessary tangents

Scoring guide:
- 5: Highly relevant - directly and completely answers the question
- 4: Mostly relevant - answers the question with minor off-topic content
- 3: Partially relevant - partially addresses the question
- 2: Mostly irrelevant - only tangentially related to the question
- 1: Completely irrelevant - does not address the question at all
"""
        )


class LanguageQualityMetric(RAGMetricBase):
    """
    Measures the language quality of the response.
    
    High quality language:
    - Clear and understandable
    - Well-structured
    - Professional tone
    """
    
    def __init__(self):
        super().__init__(
            name="language_quality",
            description="Measures clarity, structure, and professionalism of the response",
            evaluation_instructions="""
Evaluate the LANGUAGE QUALITY of the response. Language quality measures:
- Clarity: Is the response easy to understand?
- Structure: Is the response well-organized?
- Professionalism: Is the tone appropriate and professional?
- Readability: Can the reader easily follow the response?

Scoring guide:
- 5: Excellent - clear, well-structured, highly professional
- 4: Good - mostly clear and professional with minor issues
- 3: Adequate - understandable but could be improved
- 2: Poor - confusing, poorly structured, or unprofessional
- 1: Very poor - incomprehensible or highly unprofessional
"""
        )


class GrammaticalCorrectnessMetric(RAGMetricBase):
    """
    Measures grammatical correctness and readability.
    
    A grammatically correct response:
    - Has no grammatical errors
    - Uses proper punctuation
    - Has correct spelling
    - Uses clear, simple language
    """
    
    def __init__(self):
        super().__init__(
            name="grammatical_correctness",
            description="Measures grammatical correctness, spelling, and ease of understanding",
            evaluation_instructions="""
Evaluate the GRAMMATICAL CORRECTNESS of the response. This includes:
- Grammar: Are there grammatical errors?
- Spelling: Are words spelled correctly?
- Punctuation: Is punctuation used correctly?
- Simplicity: Is the language clear and easy to understand?
- Sentence structure: Are sentences well-formed and not overly complex?

Scoring guide:
- 5: Perfect - no errors, clear and simple language
- 4: Very good - minor errors that don't affect understanding
- 3: Acceptable - some errors but still understandable
- 2: Poor - multiple errors that make reading difficult
- 1: Very poor - many errors, hard to understand
"""
        )


class OverallRAGScoreMetric(RAGMetricBase):
    """
    Provides an overall evaluation of the RAG response quality.
    
    Combines all aspects: faithfulness, relevance, language quality.
    """
    
    def __init__(self):
        super().__init__(
            name="overall_rag_score",
            description="Overall evaluation combining faithfulness, relevance, and language quality",
            evaluation_instructions="""
Provide an OVERALL evaluation of the RAG response quality considering:
1. Faithfulness: Does the response stay true to the context?
2. Relevance: Does the response answer the question?
3. Language Quality: Is the response well-written and clear?
4. Grammar: Is the response grammatically correct and easy to understand?

Give a holistic score considering all these factors.

Scoring guide:
- 5: Excellent - outstanding on all dimensions
- 4: Good - strong on most dimensions with minor weaknesses
- 3: Adequate - acceptable but with room for improvement
- 2: Below average - significant issues in multiple dimensions
- 1: Poor - fails on most or all dimensions
"""
        )


# Registry of all RAG metrics
RAG_METRICS = {
    "faithfulness": FaithfulnessMetric,
    "relevance": RelevanceMetric,
    "language_quality": LanguageQualityMetric,
    "grammatical_correctness": GrammaticalCorrectnessMetric,
    "overall_rag_score": OverallRAGScoreMetric
}


def get_all_rag_metrics() -> List[BaseMetric]:
    """Get instances of all RAG metrics."""
    return [metric_class() for metric_class in RAG_METRICS.values()]


def get_rag_metric_by_name(name: str) -> Optional[BaseMetric]:
    """Get a RAG metric instance by name."""
    metric_class = RAG_METRICS.get(name)
    if metric_class:
        return metric_class()
    return None
