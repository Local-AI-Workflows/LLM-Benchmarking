from typing import List, Union, Optional
from models.base_model import BaseLLMModel
from metrics.evaluator import BaseEvaluator
from metrics.metric_base import BaseMetric
from metrics.responses import BenchmarkResult
from dataset import Dataset, Question


class BenchmarkRunner:
    """Runs benchmarks across multiple prompts and metrics."""

    def __init__(self, evaluator: Optional[BaseEvaluator], metrics: List[BaseMetric]):
        """
        Initialize the benchmark runner.
        
        Args:
            evaluator: The evaluator to use for assessing responses (can be None for email categorization)
            metrics: List of metrics to use for evaluation
        """
        self.evaluator = evaluator
        self.metrics = metrics

    async def run_benchmark(
        self, 
        model: BaseLLMModel,
        prompts: Union[List[str], Dataset]
    ) -> BenchmarkResult:
        """
        Run the benchmark for a specific model across multiple prompts.
        
        Args:
            model: The model to evaluate
            prompts: List of prompt strings or a Dataset object
            
        Returns:
            BenchmarkResult containing all evaluation results
        """
        # Convert input to standardized format
        if isinstance(prompts, Dataset):
            dataset = prompts
            prompt_strings = dataset.to_prompts()
            questions = dataset.questions
        elif isinstance(prompts, list):
            # Backward compatibility: convert list of strings to Questions
            prompt_strings = prompts
            questions = [Question.from_string(prompt) for prompt in prompts]
            dataset = Dataset(questions=questions, name="Benchmark Questions", description="Questions for benchmark evaluation")
        else:
            raise ValueError(f"Unsupported prompts type: {type(prompts)}. Expected List[str] or Dataset.")
        
        # Get responses from the model
        model_responses = {}
        model_response_objects = {}  # Store full response objects for metadata access
        for question, prompt_string in zip(questions, prompt_strings):
            response = await model.generate(prompt_string)
            # Store responses using the full prompt string as key for metrics compatibility
            model_responses[prompt_string] = response.text
            
            # Add question metadata to response object for email categorization
            if hasattr(response, 'metadata'):
                # Add expected category from question if available
                if hasattr(question, 'expected_answer') and question.expected_answer:
                    response.metadata['expected_category'] = question.expected_answer
                # Also add other question metadata
                if hasattr(question, 'metadata') and question.metadata:
                    if 'expected_category' in question.metadata:
                        response.metadata['expected_category'] = question.metadata['expected_category']
            else:
                # Create metadata if it doesn't exist
                response.metadata = {}
                if hasattr(question, 'expected_answer') and question.expected_answer:
                    response.metadata['expected_category'] = question.expected_answer
                if hasattr(question, 'metadata') and question.metadata:
                    if 'expected_category' in question.metadata:
                        response.metadata['expected_category'] = question.metadata['expected_category']
            
            model_response_objects[prompt_string] = response  # Store full object for metadata

        # Run each metric
        results = []
        for metric in self.metrics:
            # Pass both text responses and full response objects with metadata
            # For email categorization, evaluator is None but still passed for interface compatibility
            result = await metric.evaluate_batch(
                prompt_strings,
                model_responses,
                self.evaluator,
                response_objects=model_response_objects  # Pass full response objects
            )
            results.append(result)
        
        # Combine results from all metrics and add dataset information
        benchmark_result = BenchmarkResult.combine(results, model.model_name)
        
        # Add dataset metadata to the benchmark result
        if hasattr(dataset, 'name') and dataset.name:
            benchmark_result.metadata["dataset_name"] = dataset.name
        if hasattr(dataset, 'description') and dataset.description:
            benchmark_result.metadata["dataset_description"] = dataset.description
        
        # Add dataset statistics for additional context
        dataset_stats = dataset.get_statistics()
        benchmark_result.metadata["dataset_stats"] = dataset_stats
        
        return benchmark_result

    async def run_benchmark_with_dataset_info(
        self,
        model: BaseLLMModel,
        dataset: Dataset
    ) -> BenchmarkResult:
        """
        Run benchmark with full dataset integration and enhanced metadata.
        
        Args:
            model: The model to evaluate  
            dataset: Dataset object containing questions
            
        Returns:
            BenchmarkResult with enhanced dataset metadata
        """
        # This method provides explicit dataset support and is the recommended approach
        # for new code that wants to leverage the full dataset functionality
        return await self.run_benchmark(model, dataset) 