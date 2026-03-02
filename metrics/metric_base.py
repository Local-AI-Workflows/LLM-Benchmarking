from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

from .evaluator import BaseEvaluator
from .responses import EvaluatorResponse, BenchmarkResult, PromptEvaluation

# Set up logger for metrics
logger = logging.getLogger(__name__)


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
    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator, response_obj: Optional[Any] = None) -> EvaluatorResponse:
        """
        Evaluate a single response.
        
        Args:
            prompt: The input prompt
            response: The model's response
            evaluator: The evaluator to use
            response_obj: Optional full response object with metadata

        Returns:
            EvaluatorResponse containing the evaluation results
        """
        pass

    async def evaluate_batch(
        self, 
        prompts: List[str], 
        responses: Dict[str, str], 
        evaluator: BaseEvaluator,
        response_objects: Optional[Dict[str, Any]] = None
    ) -> BenchmarkResult:
        """
        Evaluate a batch of responses.
        
        Args:
            prompts: List of prompts
            responses: Dictionary mapping prompts to responses
            evaluator: The evaluator to use
            response_objects: Optional dictionary mapping prompts to full response objects with metadata

        Returns:
            BenchmarkResult containing all evaluations
        """
        prompt_evaluations = []
        
        logger.info(f"Starting batch evaluation for {self.name} metric with {len(prompts)} prompts")
        
        for i, prompt in enumerate(prompts):
            try:
                response = responses[prompt]
                response_obj = response_objects.get(prompt) if response_objects else None
                evaluation = await self.evaluate(prompt, response, evaluator, response_obj=response_obj)
                
                # Extract metadata from response object for PromptEvaluation
                pe_metadata = {}
                if response_obj and hasattr(response_obj, 'metadata') and response_obj.metadata:
                    # Copy relevant fields (like original_query for RAG)
                    pe_metadata = dict(response_obj.metadata)

                prompt_evaluations.append(PromptEvaluation(
                    prompt=prompt,
                    response=response,
                    evaluations=[evaluation],
                    metadata=pe_metadata
                ))
                
                logger.debug(f"Completed evaluation {i+1}/{len(prompts)} for {self.name}")
                
            except Exception as e:
                logger.error(f"Failed to evaluate prompt {i+1} for {self.name}: {e}")
                # Create a failed evaluation response
                from .responses import IndividualResponse
                failed_response = EvaluatorResponse(
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
                # Extract metadata from response object for failed case too
                fail_metadata = {}
                if response_objects:
                    response_obj = response_objects.get(prompt)
                    if response_obj and hasattr(response_obj, 'metadata') and response_obj.metadata:
                        fail_metadata = dict(response_obj.metadata)
                prompt_evaluations.append(PromptEvaluation(
                    prompt=prompt,
                    response=responses.get(prompt, ""),
                    evaluations=[failed_response],
                    metadata=fail_metadata
                ))
        
        # Get evaluator model names
        evaluator_models = []
        if hasattr(evaluator, 'models'):
            evaluator_models = [model.model_name for model in evaluator.models]
        elif hasattr(evaluator, 'model_name'):
            evaluator_models = [evaluator.model_name]
        
        logger.info(f"Completed batch evaluation for {self.name} metric")
        
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
    """Enhanced base class for standard metrics that follow a common evaluation pattern."""
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        evaluation_instructions: str,
        scale_min: int = 0,
        scale_max: int = 10,
        custom_format: Optional[str] = None,
        additional_context: Optional[str] = None
    ):
        """
        Initialize the metric.
        
        Args:
            name: Name of the metric
            description: Description of what the metric measures
            evaluation_instructions: Instructions for the evaluator model
            scale_min: Minimum score value (default: 0)
            scale_max: Maximum score value (default: 10)
            custom_format: Custom response format (optional)
            additional_context: Additional context for evaluation (optional)
        """
        super().__init__(name, description)
        self.evaluation_instructions = evaluation_instructions
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.custom_format = custom_format or self._default_format()
        self.additional_context = additional_context
    
    def _default_format(self) -> str:
        """Generate the default response format."""
        return f"""Your response must follow this exact format:
Score: [your score from {self.scale_min} to {self.scale_max}]

Rationale: [your explanation of the score, including specific examples]"""
    
    def _build_evaluation_prompt(self, prompt: str, response: str, response_obj: Optional[Any] = None) -> str:
        """Build the complete evaluation prompt with optional metadata context."""
        parts = [
            f"You are evaluating {self.name} in a model's response.",
            "",
            "### Prompt:",
            prompt,
            "",
            "### Response:",
            response,
            ""
        ]
        
        # Add metadata information if available
        if response_obj and hasattr(response_obj, 'metadata') and response_obj.metadata:
            metadata_info = []

            # Check for tool calls
            if 'tool_calls' in response_obj.metadata:
                tool_calls = response_obj.metadata['tool_calls']
                if tool_calls:
                    metadata_info.append(f"Tool calls made: {len(tool_calls)}")
                    for i, tc in enumerate(tool_calls, 1):
                        tool_name = tc.get('name', 'unknown')
                        tool_params = tc.get('parameters', {})
                        metadata_info.append(f"  {i}. {tool_name} with parameters: {tool_params}")
                else:
                    metadata_info.append("Tool calls made: 0 (No tools were used)")
            else:
                metadata_info.append("Tool calls made: 0 (No tools were used)")

            # Check for original response before tool execution
            if 'original_response' in response_obj.metadata:
                metadata_info.append(f"Original model response: {response_obj.metadata['original_response'][:200]}...")

            if metadata_info:
                parts.extend([
                    "### Response Metadata:",
                    "\n".join(metadata_info),
                    ""
                ])

        if self.additional_context:
            parts.extend([
                "### Additional Context:",
                self.additional_context,
                ""
            ])
        
        parts.extend([
            self.evaluation_instructions,
            "",
            self.custom_format
        ])
        
        return "\n".join(parts)
    
    async def evaluate(self, prompt: str, response: str, evaluator: BaseEvaluator, response_obj: Optional[Any] = None) -> EvaluatorResponse:
        """
        Evaluate a response using the standard evaluation pattern.
        
        Args:
            prompt: The input prompt
            response: The model's response
            evaluator: The evaluator to use
            response_obj: Optional full response object with metadata

        Returns:
            EvaluatorResponse containing the evaluation results
        """
        eval_prompt = self._build_evaluation_prompt(prompt, response, response_obj)

        logger.debug(f"Evaluating {self.name} for prompt: {prompt[:50]}...")
        
        try:
            eval_response = await evaluator.evaluate(
                evaluation=eval_prompt,
                metric_name=self.name,
                metric_description=self.description
            )

            # Add standard metadata
            eval_response.metadata.update({
                "prompt_length": len(prompt),
                "response_length": len(response),
                "scale_min": self.scale_min,
                "scale_max": self.scale_max,
                "metric_version": "1.0"
            })
            
            # Add tool call information to metadata if available
            if response_obj and hasattr(response_obj, 'metadata') and 'tool_calls' in response_obj.metadata:
                eval_response.metadata['tool_calls_made'] = len(response_obj.metadata['tool_calls'])
                eval_response.metadata['had_tool_calls'] = len(response_obj.metadata['tool_calls']) > 0
            else:
                eval_response.metadata['tool_calls_made'] = 0
                eval_response.metadata['had_tool_calls'] = False

            # Validate score is within expected range
            if not (self.scale_min <= eval_response.score <= self.scale_max):
                logger.warning(
                    f"Score {eval_response.score} for {self.name} is outside expected range "
                    f"[{self.scale_min}, {self.scale_max}]. Clamping to valid range."
                )
                eval_response.score = max(self.scale_min, min(self.scale_max, eval_response.score))
            
            logger.debug(f"Completed {self.name} evaluation with score: {eval_response.score}")
            return eval_response
            
        except Exception as e:
            logger.error(f"Failed to evaluate {self.name}: {e}")
            raise


class EvaluatorContext:
    """Context manager for handling evaluator resources."""
    
    def __init__(self, evaluator: BaseEvaluator):
        """
        Initialize the context manager.
        
        Args:
            evaluator: The evaluator to manage
        """
        self.evaluator = evaluator
    
    async def __aenter__(self):
        """Enter the async context."""
        logger.debug("Entering evaluator context")
        return self.evaluator
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context."""
        logger.debug("Exiting evaluator context")
        # Cleanup if needed - for now, just log
        if exc_type:
            logger.error(f"Exception in evaluator context: {exc_type.__name__}: {exc_val}")
        return False  # Don't suppress exceptions 