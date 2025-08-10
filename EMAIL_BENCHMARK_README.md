# Email Response Quality Benchmark

A specialized benchmark for evaluating Large Language Model (LLM) performance on professional email response generation across various business scenarios.

## Overview

This benchmark evaluates LLMs on their ability to generate appropriate, professional, and effective email responses across 20 different business communication scenarios. It uses 4 custom metrics specifically designed for email communication evaluation.

## Features

- **20 Email Scenarios**: Covering various business contexts including sales, customer service, HR, project management, and crisis communication
- **4 Custom Metrics**: Specialized evaluation criteria for email communication
- **Comprehensive Evaluation**: Multiple evaluator models for robust assessment
- **Rich Visualizations**: Interactive HTML dashboard and static charts
- **Detailed Analytics**: Performance breakdowns by email type, difficulty, and scenario

## Dataset

The benchmark includes 20 carefully crafted email scenarios covering:

### Email Types
- **Internal**: Communications within an organization
- **External**: Communications with clients, partners, vendors

### Scenarios
- Sales inquiries and rejections
- Customer complaints and support
- Project management and deadlines
- HR and policy communications
- Crisis and incident management
- Training and development follow-ups
- Partnership negotiations
- Success celebrations and recognition

### Difficulty Levels
- **Easy**: Straightforward responses with clear next steps
- **Medium**: Requires balancing multiple concerns or stakeholders
- **Hard**: Complex situations requiring careful navigation and diplomacy

## Custom Metrics

### 1. Email Professionalism (email_professionalism)
Evaluates the professional appropriateness of email responses including:
- Tone appropriateness for business context
- Structure and email etiquette
- Business-appropriate language and references
- Communication effectiveness

### 2. Email Responsiveness (email_responsiveness)
Measures how well the response addresses the original message:
- Completeness of response to all concerns
- Appropriateness of response type and urgency
- Problem-solving orientation
- Timeliness and follow-up planning

### 3. Email Clarity (email_clarity)
Assesses the clarity and understandability of communication:
- Language clarity and simplicity
- Information organization and structure
- Conciseness and focus
- Actionability of instructions

### 4. Email Empathy (email_empathy)
Evaluates emotional intelligence and human-centered communication:
- Emotional awareness and acknowledgment
- Empathetic language and tone
- Validation and support offered
- Relationship building potential

## Usage

### Prerequisites

1. **Ollama Installation**: Ensure Ollama is installed and running
2. **Required Models**: Download the following models:
   ```bash
   ollama pull llama3.2:latest
   ollama pull deepseek-r1:1.5b
   ollama pull gemma3:1b
   ```
3. **Python Dependencies**: Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Benchmark

1. **Place the dataset file** in the project root directory (already created as `email_response_dataset.json`)

2. **Run the benchmark**:
   ```bash
   python3 email_benchmark_runner.py
   ```

3. **View results**: The script will generate:
   - JSON results file with detailed evaluations
   - Interactive HTML dashboard
   - Static visualization charts

### Expected Output

The benchmark will:
1. Load the 20 email scenarios
2. Generate responses using the test model (llama3.2:latest)
3. Evaluate each response using 4 email-specific metrics
4. Generate comprehensive results and visualizations
5. Create an interactive HTML dashboard

### Results Location

All results are saved to the `email_benchmark_results/` directory:
```
email_benchmark_results/
├── email_benchmark_results_YYYYMMDD_HHMMSS.json
├── email_benchmark_dashboard_YYYYMMDD_HHMMSS.html
└── visualizations_YYYYMMDD_HHMMSS/
    ├── overall_performance.png
    ├── metrics_comparison.png
    └── performance_by_question.png
```

## Understanding the Results

### Overall Performance
- Average scores across all 20 email scenarios
- Breakdown by individual metrics
- Comparison across different email types and difficulty levels

### Metric Analysis
- **Email Professionalism**: How well the model maintains professional standards
- **Email Responsiveness**: How completely it addresses the original concerns
- **Email Clarity**: How clear and understandable the communication is
- **Email Empathy**: How well it demonstrates emotional intelligence

### Scenario Analysis
- Performance on different types of business communications
- Identification of strengths and weaknesses by scenario type
- Difficulty-based performance patterns

## Customization

### Adding New Email Scenarios
Edit `email_response_dataset.json` to add new scenarios with the following structure:
```json
{
  "id": "email_XXX",
  "text": "Original email message...",
  "context": "Response context...",
  "instructions": "Response instructions...",
  "expected_answer": "Expected response description...",
  "metadata": {
    "domain": "email_communication",
    "type": "scenario_type",
    "difficulty": "easy|medium|hard",
    "email_type": "internal|external",
    "scenario": "specific_scenario"
  }
}
```

### Modifying Models
Edit `email_benchmark_runner.py` to change:
- Test model: Modify the `test_model` configuration
- Evaluator models: Update the `evaluator_models` list
- Temperature and other model parameters

### Custom Metrics
Create new metrics by:
1. Adding a new metric file in the `metrics/` directory
2. Inheriting from `StandardMetric`
3. Registering in `metrics/__init__.py`
4. Adding to the `email_metrics` list in the runner

## Performance Expectations

- **Runtime**: Approximately 15-20 minutes for full benchmark
- **Model Requirements**: 
  - Test model: ~4GB RAM (llama3.2:latest)
  - Evaluator models: ~2-8GB RAM each
- **Output Size**: ~5-10MB for complete results

## Troubleshooting

### Common Issues

1. **Model not found**: Ensure all required Ollama models are downloaded
2. **Out of memory**: Reduce the number of evaluator models or use smaller models
3. **Slow performance**: Consider using faster/smaller evaluator models
4. **Connection errors**: Verify Ollama is running on the default port (11434)
5. **Timeout errors**: Increase timeout values in model configurations

### Debug Mode
Enable detailed logging by modifying the logging level in the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Testing First
If you encounter issues, try the demo script first:
```bash
python3 demo_email_benchmark.py
```

## Contributing

To extend this benchmark:
1. Add new email scenarios to the dataset
2. Create additional email-specific metrics
3. Add support for different model providers
4. Enhance the visualization capabilities

## License

This benchmark is part of the LLM Benchmark Framework and follows the same licensing terms. 