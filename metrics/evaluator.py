from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any, Optional
import re
import logging

from models.base_model import BaseLLMModel
from .responses import EvaluatorResponse, IndividualResponse

# Set up logger for evaluators
logger = logging.getLogger(__name__)


class BaseEvaluator(ABC):
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
        try:
            response = await self.model.generate(evaluation)
            
            # Filter out think blocks if present
            text = response.text
            think_pattern = r'<think>.*?</think>'
            text = re.sub(think_pattern, '', text, flags=re.DOTALL)
            
            # Parse score and rationale
            score = self._extract_score(text)
            rationale = self._extract_rationale(text)
            
            # Validate extracted data
            if score is None:
                logger.warning(f"Could not extract score from evaluator response for {metric_name}")
                score = 0.0
            
            if not rationale or not rationale.strip():
                logger.warning(f"Could not extract rationale from evaluator response for {metric_name}")
                rationale = "No rationale provided by evaluator"
            
            # Create individual response
            individual_response = IndividualResponse(
                model_name=self.model.model_name,
                score=score,
                rationale=rationale
            )
            
            return EvaluatorResponse(
                metric_name=metric_name,
                score=score,  # For single evaluator, this is the same as the individual score
                rationale=rationale,
                individual_responses=[individual_response],
                metadata={
                    "model_name": self.model.model_name,
                    "metric_description": metric_description,
                    "raw_response": text[:500]  # Store first 500 chars for debugging
                }
            )
            
        except Exception as e:
            logger.error(f"Error during evaluation with {self.model.model_name}: {e}")
            # Return a failed evaluation response
            individual_response = IndividualResponse(
                model_name=self.model.model_name,
                score=0.0,
                rationale=f"Evaluation failed: {str(e)}"
            )
            
            return EvaluatorResponse(
                metric_name=metric_name,
                score=0.0,
                rationale=f"Evaluation failed: {str(e)}",
                individual_responses=[individual_response],
                metadata={
                    "model_name": self.model.model_name,
                    "metric_description": metric_description,
                    "error": str(e)
                }
            )
    
    def _extract_score(self, text: str) -> Optional[float]:
        """Extract the score from the evaluator's response with improved error handling."""
        # First, check if the response looks like an actual answer instead of an evaluation
        # This happens when the evaluator LLM ignores instructions and answers the query
        evaluation_indicators = ['Score:', 'score:', 'Rating:', '/10', 'out of 10', '/5', 'out of 5']
        has_evaluation = any(indicator in text for indicator in evaluation_indicators)
        
        if not has_evaluation:
            # Response doesn't look like an evaluation - might be an actual answer
            logger.warning(f"Response doesn't appear to be an evaluation (no score indicators found)")
            # Return None to indicate evaluation failed
            return None
        
        # Define score extraction patterns in order of preference
        patterns = [
            r'Score:\s*(\d+(?:\.\d+)?)',  # Score: 8.5
            r'Score\s*=\s*(\d+(?:\.\d+)?)',  # Score = 8.5
            r'(\d+(?:\.\d+)?)\s*/\s*10',  # 8.5/10 or 8.5 / 10
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*10',  # 8.5 out of 10
            r'Rating:\s*(\d+(?:\.\d+)?)',  # Rating: 8.5
            r'Grade:\s*(\d+(?:\.\d+)?)',  # Grade: 8.5
            r'(?:^|\n)\s*(\d+(?:\.\d+)?)\s*(?:/10)?(?:\n|$)',  # Standalone number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    score = float(match.group(1))
                    # Validate score range (assuming 0-10 scale)
                    if 0 <= score <= 10:
                        logger.debug(f"Extracted score: {score} using pattern: {pattern}")
                        return score
                    elif score > 10:
                        # Handle cases where score might be on a different scale
                        if score <= 100:  # Assume 0-100 scale, convert to 0-10
                            converted_score = score / 10
                            logger.debug(f"Converted score from {score} to {converted_score}")
                            return converted_score
                        else:
                            logger.warning(f"Score {score} is unusually high, clamping to 10")
                            return 10.0
                    else:
                        logger.warning(f"Score {score} is negative, clamping to 0")
                        return 0.0
                except ValueError:
                    logger.warning(f"Could not convert extracted score to float: {match.group(1)}")
                    continue
        
        # Log the text for debugging if no score found
        logger.warning(f"Could not extract score from text: {text[:200]}...")
        return None
    
    def _extract_rationale(self, text: str) -> str:
        """Extract the rationale from the evaluator's response with improved patterns."""
        # Define rationale extraction patterns
        patterns = [
            r'Rationale:\s*(.*?)(?:\n\n|\n(?=\w+:)|\Z)',  # Rationale: ... (until double newline or next section)
            r'Explanation:\s*(.*?)(?:\n\n|\n(?=\w+:)|\Z)',  # Explanation: ...
            r'Reasoning:\s*(.*?)(?:\n\n|\n(?=\w+:)|\Z)',  # Reasoning: ...
            r'Justification:\s*(.*?)(?:\n\n|\n(?=\w+:)|\Z)',  # Justification: ...
            r'Analysis:\s*(.*?)(?:\n\n|\n(?=\w+:)|\Z)',  # Analysis: ...
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                rationale = match.group(1).strip()
                if rationale:  # Make sure it's not empty
                    logger.debug(f"Extracted rationale using pattern: {pattern[:20]}...")
                    return rationale
        
        # If no clear rationale section found, try to extract meaningful content
        # Remove common prefixes and get the main content
        cleaned_text = text.strip()
        
        # Remove score lines
        cleaned_text = re.sub(r'Score:\s*\d+(?:\.\d+)?(?:/10)?', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\d+(?:\.\d+)?/10', '', cleaned_text)
        cleaned_text = re.sub(r'\d+(?:\.\d+)?\s*out\s*of\s*10', '', cleaned_text, flags=re.IGNORECASE)
        
        # Clean up whitespace
        cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        if cleaned_text:
            logger.debug("Using cleaned text as rationale")
            return cleaned_text
        
        # Last resort: return the original text
        logger.warning("Could not extract clear rationale, returning original text")
        return text.strip()


class _MultiEvaluator(BaseEvaluator):
    """Evaluator that uses multiple models and averages their scores."""
    
    def __init__(self, models: List[BaseLLMModel]):
        """
        Initialize the multi-evaluator.
        
        Args:
            models: List of models to use for evaluation
        """
        if not models:
            raise ValueError("At least one model must be provided")
        
        super().__init__(models[0])  # Use first model as base
        self.models = models
        logger.info(f"Initialized multi-evaluator with {len(models)} models")
    
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
        successful_evaluations = 0
        
        logger.debug(f"Starting multi-model evaluation with {len(self.models)} models")
        
        for i, model in enumerate(self.models):
            try:
                response = await model.generate(evaluation)
                
                # Filter out think blocks if present
                text = response.text
                think_pattern = r'<think>.*?</think>'
                text = re.sub(think_pattern, '', text, flags=re.DOTALL)
                
                # Parse score and rationale
                score = self._extract_score(text)
                rationale = self._extract_rationale(text)
                
                if score is not None:
                    total_score += score
                    successful_evaluations += 1
                else:
                    logger.warning(f"Could not extract score from model {model.model_name}")
                    score = 0.0
                
                if not rationale or not rationale.strip():
                    rationale = f"No clear rationale from {model.model_name}"
                
                individual_responses.append(IndividualResponse(
                    model_name=model.model_name,
                    score=score,
                    rationale=rationale
                ))
                
                logger.debug(f"Completed evaluation {i+1}/{len(self.models)} with {model.model_name}")
                
            except Exception as e:
                logger.error(f"Failed evaluation with model {model.model_name}: {e}")
                individual_responses.append(IndividualResponse(
                    model_name=model.model_name,
                    score=0.0,
                    rationale=f"Evaluation failed: {str(e)}"
                ))
        
        # Calculate average score
        if successful_evaluations > 0:
            average_score = total_score / successful_evaluations
            logger.debug(f"Average score: {average_score} from {successful_evaluations} successful evaluations")
        else:
            average_score = 0.0
            logger.warning("No successful evaluations, setting average score to 0")
        
        # Combine rationales from all models
        combined_rationale = "\n\n".join([
            f"**{resp.model_name}** (Score: {resp.score}):\n{resp.rationale}"
            for resp in individual_responses
        ])
        
        return EvaluatorResponse(
            metric_name=metric_name,
            score=average_score,
            rationale=combined_rationale,
            individual_responses=individual_responses,
            metadata={
                "model_name": "multi-evaluator",
                "metric_description": metric_description,
                "num_models": len(self.models),
                "successful_evaluations": successful_evaluations,
                "model_names": [model.model_name for model in self.models]
            }
        )


class EvaluatorFactory:
    """Factory for creating evaluator instances."""
    
    @staticmethod
    def create_evaluator(models: Union[BaseLLMModel, List[BaseLLMModel]]) -> BaseEvaluator:
        """
        Create an evaluator instance.
        
        Args:
            models: Single model or list of models
            
        Returns:
            BaseEvaluator instance
            
        Raises:
            ValueError: If invalid model type is provided
        """
        if isinstance(models, list):
            if not models:
                raise ValueError("Empty model list provided")
            if len(models) == 1:
                logger.info("Creating single evaluator from list with one model")
                return BaseEvaluator(models[0])
            else:
                logger.info(f"Creating multi-evaluator with {len(models)} models")
                return _MultiEvaluator(models)
        elif isinstance(models, BaseLLMModel):
            logger.info(f"Creating single evaluator with {models.model_name}")
            return BaseEvaluator(models)
        else:
            raise ValueError(f"Invalid model type: {type(models)}. Must be BaseLLMModel or List[BaseLLMModel].")
    
    @staticmethod
    def create_single_evaluator(model: BaseLLMModel) -> BaseEvaluator:
        """Create a single model evaluator."""
        return BaseEvaluator(model)
    
    @staticmethod
    def create_multi_evaluator(models: List[BaseLLMModel]) -> _MultiEvaluator:
        """Create a multi-model evaluator."""
        return _MultiEvaluator(models)
