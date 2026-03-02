#!/usr/bin/env python3
"""
Weather MCP Tool Usage Benchmark Runner

This script runs benchmark tests for evaluating LLM performance
with the fogcast-weather MCP tool. Tests two models separately
for comparison.

Models to test:
- mixtral:latest (46.7B) - Run 1
- mixtral:latest (46.7B) - Run 2 (consistency test)

Judge models:
- llama3.2:latest (3.2B)
- deepseek-r1:8b (8.0B) - Reasoning model
- mistral:instruct (7.2B)
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from models.ollama_mcp_model import OllamaWithMCPModel, OllamaMCPConfig, MCPServerConfig
from models.ollama_model import OllamaModel, OllamaConfig
from metrics import EvaluatorFactory
from metrics.database_loader import load_metrics_from_db
from benchmark.runner import BenchmarkRunner
from dashboard import generate_html_dashboard
from dataset import DatasetLoader
from database.connection import Database

# Server configuration
REMOTE_OLLAMA_URL = "http://ollama.ios.htwg-konstanz.de:11434"
MCP_WEATHER_URL = "http://ollama.ios.htwg-konstanz.de:8000"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_weather_mcp_servers():
    """Create MCP server configuration for weather tool."""
    return [
        MCPServerConfig(
            name="fogcast-weather",
            url=MCP_WEATHER_URL,
            description="Weather service for Konstanz, Germany with current conditions, forecasts, and historical data",
            available_tools=[
                "get_current_weather_summary",
                "get_future_weather_forecast",
                "get_weather_history"
            ]
        )
    ]


def create_evaluator_models():
    """Create judge models for evaluation."""
    return [
        OllamaModel(config=OllamaConfig(
            model_name="llama3.2:latest",
            base_url=REMOTE_OLLAMA_URL,
            timeout=240.0,
            temperature=0.2,
            num_ctx=4096
        )),
        OllamaModel(config=OllamaConfig(
            model_name="deepseek-r1:8b",
            base_url=REMOTE_OLLAMA_URL,
            timeout=300.0,  # Reasoning models may take longer
            temperature=0.2,
            num_ctx=8192
        )),
        OllamaModel(config=OllamaConfig(
            model_name="mistral:instruct",
            base_url=REMOTE_OLLAMA_URL,
            timeout=240.0,
            temperature=0.2,
            num_ctx=4096
        ))
    ]


async def run_benchmark_for_model(model_name: str, dataset, evaluator, metrics, results_dir):
    """Run benchmark for a single model."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Starting benchmark for model: {model_name}")
    logger.info(f"{'='*80}\n")
    
    # Configure MCP model
    mcp_config = OllamaMCPConfig(
        model_name=model_name,
        base_url=REMOTE_OLLAMA_URL,
        temperature=0.7,
        timeout=300.0,
        num_ctx=8192,
        mcp_servers=create_weather_mcp_servers(),
        max_tool_calls=5,
        tool_call_timeout=30.0
    )
    
    test_model = OllamaWithMCPModel(config=mcp_config)
    logger.info(f"Initialized MCP model: {test_model.model_name}")
    logger.info(f"Available tools: {list(test_model.available_tools.keys())}")
    
    # Run benchmark
    runner = BenchmarkRunner(evaluator, metrics)
    benchmark_start_time = datetime.now()
    
    try:
        benchmark_result = await runner.run_benchmark(test_model, dataset)
        runtime_minutes = (datetime.now() - benchmark_start_time).total_seconds() / 60
        logger.info(f"Benchmark completed in {runtime_minutes:.1f} minutes")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_safe_name = model_name.replace(":", "_").replace("/", "_")
        
        # Save JSON results
        json_path = results_dir / f"weather_mcp_{model_safe_name}_{timestamp}.json"
        benchmark_result.save_to_json_file(str(json_path))
        logger.info(f"Results saved to: {json_path}")
        
        # Generate dashboard
        dashboard_path = results_dir / f"weather_mcp_{model_safe_name}_{timestamp}.html"
        generate_html_dashboard(benchmark_result, str(dashboard_path))
        logger.info(f"Dashboard generated: {dashboard_path}")
        
        # Print summary
        print_benchmark_summary(benchmark_result, model_name)
        
        return benchmark_result
        
    except Exception as e:
        logger.error(f"Benchmark failed for {model_name}: {e}", exc_info=True)
        return None


def print_benchmark_summary(result, model_name):
    """Print a summary of benchmark results."""
    logger.info(f"\n{'='*80}")
    logger.info(f"BENCHMARK SUMMARY - {model_name}")
    logger.info(f"{'='*80}")
    
    if hasattr(result, 'metric_scores'):
        logger.info("\nMetric Scores:")
        for metric_name, score in result.metric_scores.items():
            logger.info(f"  {metric_name}: {score:.2f}/10.0")
    
    if hasattr(result, 'overall_score'):
        logger.info(f"\nOverall Score: {result.overall_score:.2f}/10.0")
    
    logger.info(f"{'='*80}\n")


async def main():
    logger.info("="*80)
    logger.info("Weather MCP Tool Usage Benchmark")
    logger.info("Testing fogcast-weather tool with multiple models")
    logger.info("="*80)
    
    # Ensure database is connected
    if not Database.is_connected():
        await Database.connect()
    
    # Setup results directory
    results_dir = Path("results/weather_mcp_benchmark")
    results_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Results directory: {results_dir}")
    
    # Dataset path
    dataset_path = ".doc/test_data/weather_mcp_test_dataset.json"

    try:
        # Load dataset
        dataset = DatasetLoader.load_from_file(dataset_path)
        logger.info(f"\nLoaded dataset: '{dataset.name}'")
        logger.info(f"Total questions: {len(dataset)}")
        
        # Print dataset statistics
        if hasattr(dataset, 'metadata') and 'difficulty_levels' in dataset.metadata:
            logger.info(f"Difficulty levels: {dataset.metadata['difficulty_levels']}")
        
        # Create evaluator (shared across all model tests)
        evaluator_models = create_evaluator_models()
        evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
        logger.info(f"\nJudge models: {[m.model_name for m in evaluator_models]}")
        
        # Create metrics - load from database
        mcp_metrics = [
            'tool_usage_accuracy',
            'information_retrieval_quality',
            'contextual_awareness',
            'tool_selection_efficiency'
        ]
        metrics = await load_metrics_from_db(metric_names=mcp_metrics, metric_type="mcp")
        logger.info(f"Metrics: {[metric.name for metric in metrics]}")
        
        # Models to test (same model twice for consistency testing)
        models_to_test = [
            "mistral:latest",      # Run 1
            "mixtral:latest"       # Run 2
        ]
        
        logger.info(f"\nModels to test: {models_to_test}")
        logger.info("\nNote: Running same model twice to test consistency")

        # Run benchmarks for each model
        results = {}
        for model_name in models_to_test:
            result = await run_benchmark_for_model(
                model_name, 
                dataset, 
                evaluator, 
                metrics, 
                results_dir
            )
            if result:
                results[model_name] = result
            
            # Add delay between models to avoid overloading server
            if model_name != models_to_test[-1]:
                logger.info("\nWaiting 10 seconds before testing next model...\n")
                await asyncio.sleep(10)
        
        # Final summary
        logger.info("\n" + "="*80)
        logger.info("ALL BENCHMARKS COMPLETED")
        logger.info("="*80)
        logger.info(f"\nSuccessfully tested {len(results)}/{len(models_to_test)} models")
        logger.info(f"Results saved to: {results_dir}")
        
        if len(results) > 1:
            logger.info("\nComparison Summary:")
            for model_name, result in results.items():
                if hasattr(result, 'overall_score'):
                    logger.info(f"  {model_name}: {result.overall_score:.2f}/10.0")
        
        logger.info("\nYou can compare the results by opening the HTML dashboards.")
        logger.info("="*80 + "\n")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Dataset file not found: {e}")
        logger.error(f"Please ensure '{dataset_path}' exists in the current directory")
        return 1
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        return 1
    finally:
        # Ensure database is disconnected
        if Database.is_connected():
            await Database.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
