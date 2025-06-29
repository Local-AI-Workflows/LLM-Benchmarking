# Testing Framework Documentation

This document provides comprehensive information about the testing framework for the LLM Benchmark project.

## Overview

The testing framework is built using `pytest` and follows Python testing best practices. It includes:

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **Mocking**: Isolate components from external dependencies
- **Coverage reporting**: Track test coverage
- **Code quality**: Linting, formatting, and type checking
- **CI/CD**: Automated testing on GitHub Actions

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── test_models/                # Model component tests
│   ├── __init__.py
│   ├── test_model_config.py    # Configuration classes
│   ├── test_ollama_model.py    # Ollama model implementation
│   └── test_openai_model.py    # OpenAI model implementation
└── test_metrics/               # Metrics component tests
    ├── __init__.py
    ├── test_responses.py       # Response classes and validation
    └── test_factory.py         # Metric factory and registry
```

## Running Tests

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all unit tests
python run_tests.py --unit

# Run with coverage
python run_tests.py --unit --coverage

# Quick test run (no coverage)
python run_tests.py --quick
```

### Test Runner Options

The `run_tests.py` script provides various testing options:

```bash
# Run specific test types
python run_tests.py --unit          # Unit tests only
python run_tests.py --integration   # Integration tests only
python run_tests.py --all           # All tests

# Run specific test file
python run_tests.py --test tests/test_models/test_model_config.py

# Code quality checks
python run_tests.py --lint          # Linting checks
python run_tests.py --type-check    # Type checking

# Coverage and reporting
python run_tests.py --coverage      # Generate coverage report
python run_tests.py --ci            # Full CI pipeline

# Additional options
python run_tests.py --verbose       # Verbose output
python run_tests.py --parallel      # Parallel execution
```

### Direct pytest Usage

You can also run tests directly with pytest:

```bash
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run with coverage
pytest --cov --cov-report=html

# Run specific test file
pytest tests/test_models/test_model_config.py

# Run specific test
pytest tests/test_models/test_model_config.py::TestOllamaConfig::test_default_config

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Unit tests focus on testing individual components in isolation:

- **Configuration classes**: Validation, serialization, defaults
- **Model implementations**: Logic without external API calls
- **Metric factories**: Creation and registry functionality
- **Response objects**: Pydantic validation and processing

**Characteristics:**
- Fast execution (< 1 second per test)
- No external dependencies
- Extensive use of mocking
- High coverage of edge cases

### Integration Tests (`@pytest.mark.integration`)

Integration tests verify component interactions:

- **Model-to-API communication**: With mocked responses
- **End-to-end evaluation flows**: With test data
- **Configuration integration**: Real config loading

**Characteristics:**
- Slower execution (1-10 seconds per test)
- May use external test services
- Focus on realistic scenarios
- Test data flows between components

## Mocking Strategy

### Why Mock?

- **Isolation**: Test only the component logic, not external services
- **Speed**: Avoid slow network calls and API rate limits
- **Reliability**: Tests don't fail due to external service issues
- **Cost**: Avoid charges from API providers during testing

### Mocking Patterns

#### HTTP API Calls

```python
# Using aioresponses for async HTTP calls
from aioresponses import aioresponses

@pytest.mark.asyncio
async def test_ollama_generate():
    model = OllamaModel()
    
    with aioresponses() as m:
        m.post(
            "http://localhost:11434/api/generate",
            status=200,
            body='{"response": "test", "done": true}'
        )
        
        result = await model.generate("test prompt")
        assert result.text == "test"
```

#### OpenAI API Calls

```python
# Using patch for OpenAI API
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_openai_generate():
    model = OpenAIModel()
    
    with patch('openai.ChatCompletion.acreate', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = create_mock_response()
        
        result = await model.generate("test prompt")
        assert result.text == "expected response"
```

#### Complex Object Mocking

```python
# Mock complex objects with proper structure
def create_mock_response():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "test response"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.dict.return_value = {"total_tokens": 50}
    return mock_response
```

## Fixtures and Test Data

### Shared Fixtures (`conftest.py`)

Common fixtures available to all tests:

```python
# Configuration fixtures
def test_with_ollama_config(ollama_config):
    assert ollama_config.model_name == "test-llama"

# Mock objects
def test_with_mock_model(mock_llm_model):
    result = await mock_llm_model.generate("test")
    assert isinstance(result, ModelResponse)

# Test data
def test_with_sample_data(sample_questions, sample_dataset):
    assert len(sample_questions) == 3
    assert sample_dataset.name == "Test Dataset"
```

### Test Data Factories

Use factories for creating test data:

```python
def test_question_factory(question_factory):
    # Create single question
    question = question_factory.create(text="Custom question?")
    
    # Create batch of questions
    questions = question_factory.create_batch(count=5)
    assert len(questions) == 5
```

## Coverage Requirements

### Coverage Targets

- **Overall coverage**: 80% minimum
- **Unit tests**: 90%+ coverage for core logic
- **Integration tests**: Focus on critical paths

### Coverage Reports

```bash
# Generate HTML coverage report
python run_tests.py --coverage

# View report
open htmlcov/index.html
```

### Coverage Configuration

Coverage settings in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["metrics", "models", "dataset", "benchmark"]
omit = ["*/tests/*", "*/test_*.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

## Code Quality

### Formatting (Black)

```bash
# Check formatting
python -m black --check .

# Auto-format code
python -m black .
```

### Import Sorting (isort)

```bash
# Check import sorting
python -m isort --check-only --diff .

# Auto-sort imports
python -m isort .
```

### Linting (Flake8)

```bash
# Run linting
python -m flake8 . --max-line-length=100
```

### Type Checking (MyPy)

```bash
# Run type checking
python -m mypy metrics/ models/
```

## Best Practices

### Writing Good Tests

1. **Descriptive names**: Test names should describe what is being tested
   ```python
   def test_score_validation_clamps_values_to_valid_range():
   ```

2. **Arrange-Act-Assert pattern**:
   ```python
   def test_metric_creation():
       # Arrange
       factory = MetricFactory()
       
       # Act
       metric = factory.create_metric("relevance")
       
       # Assert
       assert isinstance(metric, StandardMetric)
       assert metric.name == "relevance"
   ```

3. **Test one thing**: Each test should verify one specific behavior

4. **Use fixtures**: Leverage pytest fixtures for common setup

5. **Mock external dependencies**: Don't test external services

### Test Organization

1. **Group related tests**: Use test classes for related functionality
   ```python
   class TestOllamaConfig:
       def test_default_values(self):
           # Test default configuration
       
       def test_custom_values(self):
           # Test custom configuration
   ```

2. **Use markers**: Mark tests appropriately
   ```python
   @pytest.mark.unit
   @pytest.mark.asyncio
   async def test_async_function():
   ```

3. **Parametrize tests**: Test multiple inputs efficiently
   ```python
   @pytest.mark.parametrize("input,expected", [
       ("relevance", "relevance"),
       ("RELEVANCE", "relevance"),
       ("Relevance", "relevance"),
   ])
   def test_name_normalization(input, expected):
       result = normalize_name(input)
       assert result == expected
   ```

### Error Testing

Test error conditions thoroughly:

```python
def test_invalid_metric_name_raises_error():
    with pytest.raises(ValueError) as exc_info:
        MetricFactory.create_metric("nonexistent")
    
    assert "Unknown metric" in str(exc_info.value)
    assert "nonexistent" in str(exc_info.value)
```

## Continuous Integration

### GitHub Actions

The project uses GitHub Actions for CI/CD:

- **Multi-Python testing**: Tests run on Python 3.8-3.11
- **Code quality checks**: Linting, formatting, type checking
- **Security scanning**: Bandit and Safety checks
- **Coverage reporting**: Codecov integration

### Local CI Simulation

Run the full CI pipeline locally:

```bash
python run_tests.py --ci
```

## Debugging Tests

### Running Specific Tests

```bash
# Run single test
pytest tests/test_models/test_model_config.py::TestOllamaConfig::test_default_config

# Run tests matching pattern
pytest -k "test_config"

# Run failed tests only
pytest --lf
```

### Debug Output

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb
```

### VS Code Integration

Add to `.vscode/settings.json`:

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```

## Performance Testing

### Test Performance

Monitor test execution time:

```bash
# Show slowest tests
pytest --durations=10

# Fail tests that take too long
pytest --timeout=30
```

### Parallel Execution

```bash
# Run tests in parallel
pytest -n auto

# Or using the test runner
python run_tests.py --all --parallel
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure PYTHONPATH includes project root
2. **Async test failures**: Use `@pytest.mark.asyncio`
3. **Mock not working**: Check mock target path
4. **Coverage too low**: Add tests for uncovered lines

### Getting Help

1. Check test output for specific error messages
2. Use `pytest --collect-only` to see discovered tests
3. Run with `-v` for verbose output
4. Check fixture definitions in `conftest.py`

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Add appropriate markers (`@pytest.mark.unit`, etc.)
3. Include docstrings for test classes and complex tests
4. Mock external dependencies
5. Aim for high coverage of new code
6. Run the full test suite before submitting

For questions or issues with the testing framework, please create an issue in the project repository. 