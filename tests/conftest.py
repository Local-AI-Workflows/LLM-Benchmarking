"""
Pytest configuration and shared fixtures for the LLM Benchmark Framework tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List
from pydantic import BaseModel

# Import the components we'll be testing
from models.base_model import BaseLLMModel
from models.model_config import OllamaConfig, OpenAIConfig
from metrics.responses import ModelResponse, IndividualResponse, EvaluatorResponse, BenchmarkResult, PromptEvaluation
from dataset import Question, Dataset


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_model_response():
    """Create a mock ModelResponse for testing."""
    return ModelResponse(
        text="This is a test response from the model.",
        metadata={
            "model": "test-model",
            "total_duration": 1000,
            "eval_count": 50
        }
    )


@pytest.fixture
def mock_llm_model():
    """Create a mock LLM model for testing."""
    mock = AsyncMock(spec=BaseLLMModel)
    mock.model_name = "test-model"
    mock.generate.return_value = ModelResponse(
        text="Mock response",
        metadata={"model": "test-model"}
    )
    return mock


@pytest.fixture
def sample_questions():
    """Create sample questions for testing."""
    return [
        Question(
            text="What is the capital of France?",
            expected_answer="Paris",
            context="Geography question",
            id="q1"
        ),
        Question(
            text="Explain quantum computing.",
            expected_answer="Quantum computing uses quantum mechanics...",
            context="Technology question",
            id="q2"
        ),
        Question(
            text="Write a Python function to sort a list.",
            expected_answer="def sort_list(lst): return sorted(lst)",
            context="Programming question",
            id="q3"
        )
    ]


@pytest.fixture
def sample_dataset(sample_questions):
    """Create a sample dataset for testing."""
    return Dataset(
        questions=sample_questions,
        name="Test Dataset",
        description="A dataset for testing purposes"
    )


@pytest.fixture
def mock_individual_response():
    """Create a mock IndividualResponse for testing."""
    return IndividualResponse(
        model_name="test-evaluator",
        score=8.5,
        rationale="This is a good response because it directly answers the question."
    )


@pytest.fixture
def mock_evaluator_response(mock_individual_response):
    """Create a mock EvaluatorResponse for testing."""
    return EvaluatorResponse(
        metric_name="relevance",
        score=8.5,
        rationale="Combined rationale from evaluators",
        individual_responses=[mock_individual_response],
        metadata={"model_name": "test-evaluator"}
    )


@pytest.fixture
def mock_prompt_evaluation(mock_evaluator_response):
    """Create a mock PromptEvaluation for testing."""
    return PromptEvaluation(
        prompt="What is AI?",
        response="AI is artificial intelligence...",
        evaluations=[mock_evaluator_response]
    )


@pytest.fixture
def mock_benchmark_result(mock_prompt_evaluation):
    """Create a mock BenchmarkResult for testing."""
    return BenchmarkResult(
        prompt_evaluations=[mock_prompt_evaluation],
        metadata={
            "model_name": "test-model",
            "num_prompts": 1,
            "metrics": ["relevance"]
        }
    )


@pytest.fixture
def ollama_config():
    """Create a test Ollama configuration."""
    return OllamaConfig(
        model_name="test-llama",
        base_url="http://localhost:11434",
        temperature=0.7,
        num_ctx=2048
    )


@pytest.fixture
def openai_config():
    """Create a test OpenAI configuration."""
    return OpenAIConfig(
        model_name="gpt-3.5-turbo",
        api_key="test-api-key",
        temperature=0.7,
        max_tokens=1000
    )


class MockAsyncContextManager:
    """Helper class for mocking async context managers."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockResponse:
    """Mock HTTP response for testing API calls."""
    
    def __init__(self, status=200, json_data=None, text_data=None):
        self.status = status
        self._json_data = json_data or {}
        self._text_data = text_data or ""
        self.content = MockContent(text_data or "")
    
    async def json(self):
        return self._json_data
    
    async def text(self):
        return self._text_data


class MockContent:
    """Mock response content for streaming responses."""
    
    def __init__(self, data):
        self.data = data.encode() if isinstance(data, str) else data
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if hasattr(self, '_exhausted'):
            raise StopAsyncIteration
        self._exhausted = True
        return self.data


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response."""
    return MockResponse(
        status=200,
        json_data={"response": "test response", "done": True},
        text_data='{"response": "test response", "done": true}'
    )


@pytest.fixture
def mock_aiohttp_session(mock_http_response):
    """Create a mock aiohttp session."""
    mock_session = AsyncMock()
    mock_session.post.return_value = MockAsyncContextManager(mock_http_response)
    return mock_session


# Test data factories
class QuestionFactory:
    """Factory for creating test questions."""
    
    @staticmethod
    def create(
        text: str = "Test question?",
        expected_answer: str = "Test answer",
        context: str = "Test context",
        **kwargs
    ) -> Question:
        """Create a test question with default or custom values."""
        return Question(
            text=text,
            expected_answer=expected_answer,
            context=context,
            **kwargs
        )
    
    @staticmethod
    def create_batch(count: int = 3) -> List[Question]:
        """Create a batch of test questions."""
        return [
            QuestionFactory.create(
                text=f"Test question {i}?",
                expected_answer=f"Test answer {i}",
                id=f"q{i}"
            )
            for i in range(1, count + 1)
        ]


@pytest.fixture
def question_factory():
    """Provide the QuestionFactory for tests."""
    return QuestionFactory


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.external = pytest.mark.external
pytest.mark.asyncio = pytest.mark.asyncio 