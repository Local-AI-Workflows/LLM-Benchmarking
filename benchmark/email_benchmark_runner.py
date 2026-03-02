"""
Specialized benchmark runner for email categorization with instructional prompts.
"""

from typing import List, Dict, Any
from models.base_model import BaseLLMModel
from metrics.metric_base import BaseMetric
from metrics.responses import BenchmarkResult, PromptEvaluation
from dataset import Dataset, Question


class EmailBenchmarkRunner:
    """
    Specialized runner for email categorization benchmarks.
    
    Supports testing with multiple instructional prompts to determine which performs best.
    """
    
    def __init__(self, metrics: List[BaseMetric]):
        """
        Initialize the email benchmark runner.
        
        Args:
            metrics: List of metrics to use for evaluation (should include EmailCategorizationMetric)
        """
        self.metrics = metrics
    
    async def run_benchmark_with_prompts(
        self,
        model: BaseLLMModel,
        dataset: Dataset,
        instructional_prompts: List[str]
    ) -> Dict[str, BenchmarkResult]:
        """
        Run email categorization benchmark with multiple instructional prompts.
        
        For each email in the dataset, tests with each instructional prompt and tracks
        which prompt performs best overall.
        
        Args:
            model: The model to evaluate
            dataset: Dataset containing emails
            instructional_prompts: List of instructional prompts to test
            
        Returns:
            Dictionary mapping instructional prompt to BenchmarkResult
        """
        results_by_prompt = {}
        
        for prompt_idx, instructional_prompt in enumerate(instructional_prompts):
            # Create prompts by combining email with instructional prompt
            prompt_strings = []
            questions = []
            
            for question in dataset.questions:
                # Build the full prompt: instructional prompt + email
                full_prompt = f"{instructional_prompt}\n\n{question.text}"
                prompt_strings.append(full_prompt)
                questions.append(question)
            
            # Get responses from the model
            model_responses = {}
            model_response_objects = {}
            
            for question, prompt_string in zip(questions, prompt_strings):
                response = await model.generate(prompt_string)
                model_responses[prompt_string] = response.text
                
                # Add question metadata to response object
                if hasattr(response, 'metadata'):
                    if hasattr(question, 'expected_answer') and question.expected_answer:
                        response.metadata['expected_category'] = question.expected_answer
                    if hasattr(question, 'metadata') and question.metadata:
                        if 'expected_category' in question.metadata:
                            response.metadata['expected_category'] = question.metadata['expected_category']
                else:
                    response.metadata = {}
                    if hasattr(question, 'expected_answer') and question.expected_answer:
                        response.metadata['expected_category'] = question.expected_answer
                    if hasattr(question, 'metadata') and question.metadata:
                        if 'expected_category' in question.metadata:
                            response.metadata['expected_category'] = question.metadata['expected_category']
                
                # Store instructional prompt info
                response.metadata['instructional_prompt'] = instructional_prompt
                response.metadata['instructional_prompt_index'] = prompt_idx
                
                model_response_objects[prompt_string] = response
            
            # Run each metric
            metric_results = []
            for metric in self.metrics:
                result = await metric.evaluate_batch(
                    prompt_strings,
                    model_responses,
                    None,  # No evaluator for email categorization
                    response_objects=model_response_objects
                )
                metric_results.append(result)
            
            # Combine results from all metrics
            if metric_results:
                benchmark_result = BenchmarkResult.combine(metric_results, model.model_name)
                benchmark_result.metadata["instructional_prompt"] = instructional_prompt
                benchmark_result.metadata["instructional_prompt_index"] = prompt_idx
                results_by_prompt[instructional_prompt] = benchmark_result
        
        return results_by_prompt
    
    def get_best_prompt(self, results_by_prompt: Dict[str, BenchmarkResult]) -> str:
        """
        Determine which instructional prompt performed best.
        
        Args:
            results_by_prompt: Dictionary mapping prompts to results
            
        Returns:
            The instructional prompt with the highest accuracy
        """
        best_prompt = None
        best_accuracy = -1.0
        
        for prompt, result in results_by_prompt.items():
            accuracy = result.metadata.get("accuracy_percentage", 0.0)
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_prompt = prompt
        
        return best_prompt


