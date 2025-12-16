"""
Email categorization metric that compares model output categories with expected categories.
This metric does not use an evaluator model - it performs direct category comparison.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from .metric_base import BaseMetric
from .responses import EvaluatorResponse, IndividualResponse, BenchmarkResult, PromptEvaluation

logger = logging.getLogger(__name__)


class EmailCategorizationMetric(BaseMetric):
    """
    Metric for email categorization that compares model output with expected categories.
    
    This metric:
    - Does not use an evaluator model
    - Directly compares model output category with expected category
    - Returns percentage scores (0-100, normalized to 0-10)
    - Supports tracking which instructional prompt performs best
    """
    
    def __init__(
        self,
        name: str = "email_categorization",
        description: str = "Email categorization accuracy metric",
        categories: Optional[List[str]] = None
    ):
        """
        Initialize the email categorization metric.
        
        Args:
            name: Metric name
            description: Metric description
            categories: List of valid categories (optional, can be extracted from dataset)
        """
        super().__init__(name, description)
        self.categories = categories or []
    
    def _extract_category(self, text: str) -> Optional[str]:
        """
        Extract category from model response.
        
        Tries multiple patterns to find the category:
        - Direct category name
        - Category in quotes
        - Category after "Category:" or similar labels
        
        Args:
            text: Model response text
            
        Returns:
            Extracted category or None
        """
        if not text:
            return None
        
        # Normalize text
        text = text.strip()
        
        # If we have a list of valid categories, try to match them
        if self.categories:
            # Try exact match (case-insensitive)
            text_lower = text.lower()
            for category in self.categories:
                if category.lower() == text_lower:
                    return category
                # Try matching with quotes or other formatting
                if f'"{category}"' in text or f"'{category}'" in text:
                    return category
                # Try matching as a word boundary
                pattern = r'\b' + re.escape(category) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    return category
        
        # Try to extract category from common patterns
        patterns = [
            r'category:\s*([^\n,;.]+)',
            r'category\s*=\s*([^\n,;.]+)',
            r'class:\s*([^\n,;.]+)',
            r'class\s*=\s*([^\n,;.]+)',
            r'label:\s*([^\n,;.]+)',
            r'label\s*=\s*([^\n,;.]+)',
            r'"([^"]+)"',  # Text in quotes
            r"'([^']+)'",  # Text in single quotes
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                category = match.group(1).strip()
                # If we have valid categories, verify it matches
                if self.categories:
                    category_lower = category.lower()
                    for valid_cat in self.categories:
                        if valid_cat.lower() == category_lower:
                            return valid_cat
                else:
                    # No validation, return as-is
                    return category
        
        # If no pattern matched, try to use the first line or first word
        first_line = text.split('\n')[0].strip()
        if first_line and len(first_line) < 100:  # Reasonable category length
            # Remove common prefixes
            first_line = re.sub(r'^(category|class|label):\s*', '', first_line, flags=re.IGNORECASE)
            first_line = first_line.strip('"\'')
            if self.categories:
                # Try to match with valid categories
                for valid_cat in self.categories:
                    if valid_cat.lower() == first_line.lower():
                        return valid_cat
            return first_line
        
        return None
    
    def _normalize_category(self, category: str) -> str:
        """
        Normalize category name for comparison.
        
        Args:
            category: Category string
            
        Returns:
            Normalized category
        """
        if not category:
            return ""
        # Convert to lowercase and strip
        normalized = category.lower().strip()
        # Remove quotes
        normalized = normalized.strip('"\'')
        return normalized
    
    def _compare_categories(self, predicted: Optional[str], expected: Optional[str]) -> bool:
        """
        Compare predicted category with expected category.
        
        Args:
            predicted: Predicted category from model
            expected: Expected category from dataset
            
        Returns:
            True if categories match, False otherwise
        """
        if not predicted or not expected:
            return False
        
        # Normalize both categories
        pred_norm = self._normalize_category(predicted)
        exp_norm = self._normalize_category(expected)
        
        return pred_norm == exp_norm
    
    async def evaluate(
        self,
        prompt: str,
        response: str,
        evaluator: Any,  # Not used, but required by interface
        response_obj: Optional[Any] = None
    ) -> EvaluatorResponse:
        """
        Evaluate a single email categorization response.
        
        Args:
            prompt: The input prompt (email + instructional prompt)
            response: The model's response (should contain a category)
            evaluator: Not used (kept for interface compatibility)
            response_obj: Optional response object with metadata
            
        Returns:
            EvaluatorResponse with score (0-10) and rationale
        """
        # Extract expected category from response_obj metadata
        # The benchmark runner sets this from the question's expected_answer or metadata
        expected_category = None
        if response_obj and hasattr(response_obj, 'metadata'):
            expected_category = response_obj.metadata.get('expected_category')
        
        # If still not found, try to extract from prompt (fallback)
        # This shouldn't normally be needed if benchmark runner is working correctly
        if not expected_category:
            # Try to find category in prompt (e.g., if it was embedded)
            # This is a fallback mechanism
            pass
        
        # Extract predicted category from response
        predicted_category = self._extract_category(response)
        
        # Compare categories
        is_correct = self._compare_categories(predicted_category, expected_category)
        
        # Score: 10 if correct, 0 if incorrect (normalized from 0-100 to 0-10)
        score = 10.0 if is_correct else 0.0
        
        # Build rationale
        if is_correct:
            rationale = f"Correctly categorized as '{predicted_category}'. Expected: '{expected_category}'."
        else:
            rationale = f"Incorrect categorization. Predicted: '{predicted_category or 'N/A'}', Expected: '{expected_category or 'N/A'}'."
        
        # Create individual response (no evaluator model used)
        individual_response = IndividualResponse(
            model_name="direct_comparison",
            score=score,
            rationale=rationale
        )
        
        # Copy metadata from response_obj if available (including instructional_prompt)
        evaluation_metadata = {
            "predicted_category": predicted_category,
            "expected_category": expected_category,
            "is_correct": is_correct,
            "evaluation_method": "direct_category_comparison"
        }
        
        # Copy instructional_prompt and other metadata from response_obj
        if response_obj and hasattr(response_obj, 'metadata'):
            if 'instructional_prompt' in response_obj.metadata:
                evaluation_metadata['instructional_prompt'] = response_obj.metadata['instructional_prompt']
            if 'instructional_prompt_index' in response_obj.metadata:
                evaluation_metadata['instructional_prompt_index'] = response_obj.metadata['instructional_prompt_index']
            # Copy email metadata if available
            if 'email_subject' in response_obj.metadata:
                evaluation_metadata['email_subject'] = response_obj.metadata['email_subject']
            if 'email_body' in response_obj.metadata:
                evaluation_metadata['email_body'] = response_obj.metadata['email_body']
            if 'email_sender' in response_obj.metadata:
                evaluation_metadata['email_sender'] = response_obj.metadata['email_sender']
        
        return EvaluatorResponse(
            metric_name=self.name,
            score=score,
            rationale=rationale,
            individual_responses=[individual_response],
            metadata=evaluation_metadata
        )
    
    async def evaluate_batch(
        self,
        prompts: List[str],
        responses: Dict[str, str],
        evaluator: Any,  # Not used, but required by interface
        response_objects: Optional[Dict[str, Any]] = None
    ) -> BenchmarkResult:
        """
        Evaluate a batch of email categorization responses.
        
        Args:
            prompts: List of prompts
            responses: Dictionary mapping prompts to responses
            evaluator: Not used (kept for interface compatibility)
            response_objects: Optional dictionary mapping prompts to response objects
            
        Returns:
            BenchmarkResult with percentage accuracy
        """
        prompt_evaluations = []
        correct_count = 0
        total_count = 0
        
        logger.info(f"Starting batch evaluation for {self.name} metric with {len(prompts)} prompts")
        
        for i, prompt in enumerate(prompts):
            try:
                response = responses[prompt]
                response_obj = response_objects.get(prompt) if response_objects else None
                
                # The expected category should be in the question's expected_answer field
                # or in the response_obj metadata. We'll pass it through the response_obj
                # metadata in the benchmark runner
                
                evaluation = await self.evaluate(prompt, response, evaluator, response_obj=response_obj)
                
                # Track correctness for percentage calculation
                if evaluation.metadata.get("is_correct", False):
                    correct_count += 1
                total_count += 1
                
                prompt_evaluations.append(PromptEvaluation(
                    prompt=prompt,
                    response=response,
                    evaluations=[evaluation]
                ))
                
                logger.debug(f"Completed evaluation {i+1}/{len(prompts)} for {self.name}")
                
            except Exception as e:
                logger.error(f"Failed to evaluate prompt {i+1} for {self.name}: {e}")
                # Create a failed evaluation response
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
                prompt_evaluations.append(PromptEvaluation(
                    prompt=prompt,
                    response=responses.get(prompt, ""),
                    evaluations=[failed_response]
                ))
                total_count += 1
        
        # Calculate percentage accuracy
        accuracy_percentage = (correct_count / total_count * 100) if total_count > 0 else 0.0
        
        logger.info(f"Completed batch evaluation for {self.name} metric. Accuracy: {accuracy_percentage:.2f}% ({correct_count}/{total_count})")
        
        return BenchmarkResult(
            prompt_evaluations=prompt_evaluations,
            metadata={
                "num_prompts": len(prompts),
                "num_metrics": 1,
                "metrics": [self.name],
                "evaluator_models": ["direct_comparison"],  # No evaluator model used
                "accuracy_percentage": accuracy_percentage,
                "correct_count": correct_count,
                "total_count": total_count
            }
        )

