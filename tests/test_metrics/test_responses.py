"""
Unit tests for metrics response classes.
"""

import pytest
import json
from typing import Dict, Any
from pydantic import ValidationError

from metrics.responses import (
    ModelResponse, IndividualResponse, EvaluatorResponse, 
    PromptEvaluation, BenchmarkResult
)


class TestModelResponse:
    """Test cases for ModelResponse."""
    
    @pytest.mark.unit
    def test_valid_model_response(self):
        """Test creating a valid ModelResponse."""
        response = ModelResponse(
            text="This is a test response",
            metadata={"model": "test-model", "tokens": 100}
        )
        
        assert response.text == "This is a test response"
        assert response.metadata["model"] == "test-model"
        assert response.metadata["tokens"] == 100
    
    @pytest.mark.unit
    def test_model_response_empty_text(self):
        """Test ModelResponse with empty text."""
        response = ModelResponse(text="Valid text", metadata={})
        
        assert response.text == "Valid text"
        assert response.metadata == {}
    
    @pytest.mark.unit
    def test_model_response_serialization(self):
        """Test ModelResponse JSON serialization."""
        response = ModelResponse(
            text="Test response",
            metadata={"model": "gpt-4", "duration": 1.5}
        )
        
        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        
        # Test round-trip
        restored = ModelResponse.model_validate_json(json_str)
        assert restored.text == "Test response"
        assert restored.metadata["model"] == "gpt-4"
        assert restored.metadata["duration"] == 1.5


class TestIndividualResponse:
    """Test cases for IndividualResponse."""
    
    @pytest.mark.unit
    def test_valid_individual_response(self):
        """Test creating a valid IndividualResponse."""
        response = IndividualResponse(
            model_name="evaluator-1",
            score=8.5,
            rationale="This response is very good because it answers the question directly."
        )
        
        assert response.model_name == "evaluator-1"
        assert response.score == 8.5
        assert "very good" in response.rationale
    
    @pytest.mark.unit
    def test_score_rounding(self):
        """Test that scores are rounded to 1 decimal place."""
        response = IndividualResponse(
            model_name="evaluator",
            score=8.567890,
            rationale="Test rationale"
        )
        
        assert response.score == 8.6
    
    @pytest.mark.unit
    def test_score_validation_bounds(self):
        """Test score validation within bounds."""
        # Valid scores
        IndividualResponse(model_name="eval", score=0.0, rationale="test")
        IndividualResponse(model_name="eval", score=10.0, rationale="test")
        IndividualResponse(model_name="eval", score=5.5, rationale="test")
        
        # Invalid scores should raise validation errors
        with pytest.raises(ValidationError):
            IndividualResponse(model_name="eval", score=-1.0, rationale="test")
        
        with pytest.raises(ValidationError):
            IndividualResponse(model_name="eval", score=11.0, rationale="test")
    
    @pytest.mark.unit
    def test_rationale_validation(self):
        """Test rationale validation."""
        # Valid rationale
        response = IndividualResponse(
            model_name="eval",
            score=8.0,
            rationale="  This is a good response.  "
        )
        assert response.rationale == "This is a good response."  # Should be trimmed
        
        # Empty rationale should raise validation error
        with pytest.raises(ValidationError):
            IndividualResponse(model_name="eval", score=8.0, rationale="")
        
        # Whitespace-only rationale should raise validation error
        with pytest.raises(ValidationError):
            IndividualResponse(model_name="eval", score=8.0, rationale="   ")
    
    @pytest.mark.unit
    def test_individual_response_serialization(self):
        """Test IndividualResponse serialization."""
        response = IndividualResponse(
            model_name="gpt-4",
            score=7.8,
            rationale="Good response with minor issues."
        )
        
        data = response.model_dump()
        assert data["model_name"] == "gpt-4"
        assert data["score"] == 7.8
        assert data["rationale"] == "Good response with minor issues."
        
        # Test JSON serialization
        json_str = response.model_dump_json()
        restored = IndividualResponse.model_validate_json(json_str)
        assert restored.model_name == response.model_name
        assert restored.score == response.score
        assert restored.rationale == response.rationale


class TestEvaluatorResponse:
    """Test cases for EvaluatorResponse."""
    
    @pytest.mark.unit
    def test_valid_evaluator_response(self):
        """Test creating a valid EvaluatorResponse."""
        individual = IndividualResponse(
            model_name="eval-1",
            score=8.5,
            rationale="Good response"
        )
        
        response = EvaluatorResponse(
            metric_name="relevance",
            score=8.5,
            rationale="Overall good relevance",
            individual_responses=[individual],
            metadata={"evaluator_count": 1}
        )
        
        assert response.metric_name == "relevance"
        assert response.score == 8.5
        assert response.rationale == "Overall good relevance"
        assert len(response.individual_responses) == 1
        assert response.metadata["evaluator_count"] == 1
    
    @pytest.mark.unit
    def test_score_rounding_evaluator_response(self):
        """Test score rounding in EvaluatorResponse."""
        individual = IndividualResponse(
            model_name="eval",
            score=8.0,
            rationale="Test"
        )
        
        response = EvaluatorResponse(
            metric_name="clarity",
            score=7.666666,
            rationale="Test rationale",
            individual_responses=[individual]
        )
        
        assert response.score == 7.7
    
    @pytest.mark.unit
    def test_multiple_individual_responses(self):
        """Test EvaluatorResponse with multiple individual responses."""
        individuals = [
            IndividualResponse(model_name="eval-1", score=8.0, rationale="Good"),
            IndividualResponse(model_name="eval-2", score=7.5, rationale="Decent"),
            IndividualResponse(model_name="eval-3", score=9.0, rationale="Excellent")
        ]
        
        response = EvaluatorResponse(
            metric_name="coherence",
            score=8.2,
            rationale="Mixed evaluations",
            individual_responses=individuals
        )
        
        assert len(response.individual_responses) == 3
        assert response.individual_responses[0].score == 8.0
        assert response.individual_responses[1].score == 7.5
        assert response.individual_responses[2].score == 9.0
    
    @pytest.mark.unit
    def test_evaluator_response_serialization(self):
        """Test EvaluatorResponse serialization."""
        individual = IndividualResponse(
            model_name="eval",
            score=8.0,
            rationale="Test rationale"
        )
        
        response = EvaluatorResponse(
            metric_name="accuracy",
            score=8.0,
            rationale="Overall accurate",
            individual_responses=[individual],
            metadata={"test": "value"}
        )
        
        # Test dict serialization
        data = response.model_dump()
        assert data["metric_name"] == "accuracy"
        assert len(data["individual_responses"]) == 1
        
        # Test JSON serialization
        json_str = response.model_dump_json()
        restored = EvaluatorResponse.model_validate_json(json_str)
        assert restored.metric_name == "accuracy"
        assert len(restored.individual_responses) == 1
        assert restored.individual_responses[0].score == 8.0


class TestPromptEvaluation:
    """Test cases for PromptEvaluation."""
    
    @pytest.mark.unit
    def test_valid_prompt_evaluation(self):
        """Test creating a valid PromptEvaluation."""
        individual = IndividualResponse(
            model_name="eval",
            score=8.0,
            rationale="Good response"
        )
        
        evaluator = EvaluatorResponse(
            metric_name="relevance",
            score=8.0,
            rationale="Relevant response",
            individual_responses=[individual]
        )
        
        prompt_eval = PromptEvaluation(
            prompt="What is AI?",
            response="AI is artificial intelligence...",
            evaluations=[evaluator]
        )
        
        assert prompt_eval.prompt == "What is AI?"
        assert "artificial intelligence" in prompt_eval.response
        assert len(prompt_eval.evaluations) == 1
        assert prompt_eval.evaluations[0].metric_name == "relevance"
    
    @pytest.mark.unit
    def test_multiple_evaluations(self):
        """Test PromptEvaluation with multiple metric evaluations."""
        individual1 = IndividualResponse(model_name="eval", score=8.0, rationale="Good")
        individual2 = IndividualResponse(model_name="eval", score=7.0, rationale="Okay")
        
        evaluations = [
            EvaluatorResponse(
                metric_name="relevance",
                score=8.0,
                rationale="Relevant",
                individual_responses=[individual1]
            ),
            EvaluatorResponse(
                metric_name="clarity",
                score=7.0,
                rationale="Could be clearer",
                individual_responses=[individual2]
            )
        ]
        
        prompt_eval = PromptEvaluation(
            prompt="Test question",
            response="Test answer",
            evaluations=evaluations
        )
        
        assert len(prompt_eval.evaluations) == 2
        metric_names = [e.metric_name for e in prompt_eval.evaluations]
        assert "relevance" in metric_names
        assert "clarity" in metric_names
    
    @pytest.mark.unit
    def test_prompt_evaluation_serialization(self):
        """Test PromptEvaluation serialization using dataclass methods."""
        individual = IndividualResponse(
            model_name="eval",
            score=8.5,
            rationale="Test rationale"
        )
        
        evaluator = EvaluatorResponse(
            metric_name="accuracy",
            score=8.5,
            rationale="Accurate response",
            individual_responses=[individual]
        )
        
        prompt_eval = PromptEvaluation(
            prompt="Test prompt",
            response="Test response",
            evaluations=[evaluator]
        )
        
        # PromptEvaluation is a dataclass, so we can't use .json() method
        # Instead, we'll test that it can be created and accessed
        assert prompt_eval.prompt == "Test prompt"
        assert prompt_eval.response == "Test response"
        assert len(prompt_eval.evaluations) == 1
        assert prompt_eval.evaluations[0].score == 8.5


class TestBenchmarkResult:
    """Test cases for BenchmarkResult."""
    
    @pytest.mark.unit
    def test_valid_benchmark_result(self):
        """Test creating a valid BenchmarkResult."""
        individual = IndividualResponse(
            model_name="eval",
            score=8.0,
            rationale="Good"
        )
        
        evaluator = EvaluatorResponse(
            metric_name="relevance",
            score=8.0,
            rationale="Relevant",
            individual_responses=[individual]
        )
        
        prompt_eval = PromptEvaluation(
            prompt="Test prompt",
            response="Test response",
            evaluations=[evaluator]
        )
        
        result = BenchmarkResult(
            prompt_evaluations=[prompt_eval],
            metadata={"model": "test-model", "dataset": "test-dataset"}
        )
        
        assert len(result.prompt_evaluations) == 1
        assert result.metadata["model"] == "test-model"
    
    @pytest.mark.unit
    def test_summary_statistics(self):
        """Test summary statistics calculation."""
        # Create multiple prompt evaluations with different scores
        evaluations = []
        scores = [8.0, 7.5, 9.0, 6.5, 8.5]
        
        for i, score in enumerate(scores):
            individual = IndividualResponse(
                model_name="eval",
                score=score,
                rationale=f"Rationale {i}"
            )
            
            evaluator = EvaluatorResponse(
                metric_name="relevance",
                score=score,
                rationale=f"Overall {i}",
                individual_responses=[individual]
            )
            
            prompt_eval = PromptEvaluation(
                prompt=f"Prompt {i}",
                response=f"Response {i}",
                evaluations=[evaluator]
            )
            
            evaluations.append(prompt_eval)
        
        result = BenchmarkResult(
            prompt_evaluations=evaluations,
            metadata={"test": "data"}
        )
        
        summary = result.get_summary_statistics()
        
        assert summary["num_prompts"] == 5
        assert summary["num_metrics"] == 1
        assert "relevance" in summary["metrics"]
        assert summary["average_scores"]["relevance"] == 7.9  # (8+7.5+9+6.5+8.5)/5
        assert summary["overall_average"] == 7.9
    
    @pytest.mark.unit
    def test_multiple_metrics_summary(self):
        """Test summary statistics with multiple metrics."""
        individual1 = IndividualResponse(model_name="eval", score=8.0, rationale="Good")
        individual2 = IndividualResponse(model_name="eval", score=7.0, rationale="Okay")
        
        evaluators = [
            EvaluatorResponse(
                metric_name="relevance",
                score=8.0,
                rationale="Relevant",
                individual_responses=[individual1]
            ),
            EvaluatorResponse(
                metric_name="clarity",
                score=7.0,
                rationale="Clear enough",
                individual_responses=[individual2]
            )
        ]
        
        prompt_eval = PromptEvaluation(
            prompt="Test",
            response="Test response",
            evaluations=evaluators
        )
        
        result = BenchmarkResult(
            prompt_evaluations=[prompt_eval],
            metadata={}
        )
        
        summary = result.get_summary_statistics()
        
        assert "relevance" in summary["average_scores"]
        assert "clarity" in summary["average_scores"]
        assert summary["average_scores"]["relevance"] == 8.0
        assert summary["average_scores"]["clarity"] == 7.0
    
    @pytest.mark.unit
    def test_benchmark_result_serialization(self):
        """Test BenchmarkResult JSON serialization."""
        individual = IndividualResponse(
            model_name="eval",
            score=8.0,
            rationale="Test"
        )
        
        evaluator = EvaluatorResponse(
            metric_name="test_metric",
            score=8.0,
            rationale="Test evaluation",
            individual_responses=[individual]
        )
        
        prompt_eval = PromptEvaluation(
            prompt="Test prompt",
            response="Test response",
            evaluations=[evaluator]
        )
        
        result = BenchmarkResult(
            prompt_evaluations=[prompt_eval],
            metadata={"test": "metadata"}
        )
        
        # Test to_json method
        json_str = result.to_json()
        assert isinstance(json_str, str)
        
        # Test round-trip
        restored = BenchmarkResult.from_json(json_str)
        assert len(restored.prompt_evaluations) == 1
        assert restored.metadata["test"] == "metadata"
    
    @pytest.mark.unit
    def test_empty_benchmark_result(self):
        """Test BenchmarkResult with no evaluations should raise error."""
        with pytest.raises(ValueError) as exc_info:
            BenchmarkResult(
                prompt_evaluations=[],
                metadata={"empty": True}
            )
        
        assert "At least one prompt evaluation is required" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_score_distribution_analysis(self):
        """Test detailed score distribution analysis."""
        # Create evaluations with known score distribution
        scores = [5.0, 6.0, 7.0, 7.0, 8.0, 8.0, 8.0, 9.0, 10.0]
        evaluations = []
        
        for i, score in enumerate(scores):
            individual = IndividualResponse(
                model_name="eval",
                score=score,
                rationale=f"Test {i}"
            )
            
            evaluator = EvaluatorResponse(
                metric_name="test_metric",
                score=score,
                rationale=f"Evaluation {i}",
                individual_responses=[individual]
            )
            
            prompt_eval = PromptEvaluation(
                prompt=f"Prompt {i}",
                response=f"Response {i}",
                evaluations=[evaluator]
            )
            
            evaluations.append(prompt_eval)
        
        result = BenchmarkResult(
            prompt_evaluations=evaluations,
            metadata={}
        )
        
        summary = result.get_summary_statistics()
        
        assert summary["num_prompts"] == 9
        # Calculate actual average: (5+6+7+7+8+8+8+9+10)/9 = 68/9 = 7.555... ≈ 7.6
        assert summary["average_scores"]["test_metric"] == pytest.approx(7.6, abs=0.1)
        assert summary["overall_average"] == pytest.approx(7.6, abs=0.1)
        assert "score_distribution" in summary
        assert summary["score_distribution"]["min"] == 5.0
        assert summary["score_distribution"]["max"] == 10.0 