#!/usr/bin/env python3
"""
MCP Tool Usage Benchmark Runner

This script runs a benchmark test for evaluating LLM performance
on MCP (Model Context Protocol) tool usage with weather and mensa services.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from models.ollama_mcp_model import OllamaWithMCPModel, OllamaMCPConfig, MCPServerConfig
from metrics import MetricFactory, EvaluatorFactory
from benchmark.runner import BenchmarkRunner
from dashboard import generate_html_dashboard
from dataset import DatasetLoader

# MCP Server configuration
REMOTE_OLLAMA_URL = "http://ollama.ios.htwg-konstanz.de:11434"
MCP_WEATHER_URL = "http://ollama.ios.htwg-konstanz.de:8007"
MCP_MENSA_URL = "http://ollama.ios.htwg-konstanz.de:8008"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting MCP Tool Usage Benchmark")

    results_dir = Path(".doc/benchmark_results/mcp_benchmark_results")
    results_dir.mkdir(exist_ok=True)

    try:
        # Load dataset
        dataset = DatasetLoader.load_from_file(".doc/test_data/mcp_test_dataset.json")
        logger.info(f"Loaded dataset '{dataset.name}' with {len(dataset)} scenarios")

        # MCP server configs
        mcp_servers = [
            MCPServerConfig(
                name="weather",
                url=MCP_WEATHER_URL,
                description="Weather data and forecasts",
                available_tools=["get_weather", "get_forecast"]
            ),
            MCPServerConfig(
                name="mensa",
                url=MCP_MENSA_URL,
                description="Cafeteria menu information",
                available_tools=["get_menu", "get_daily_menu"]
            )
        ]

        # MCP-enabled test model
        mcp_config = OllamaMCPConfig(
            model_name="mixtral:latest",
            base_url=REMOTE_OLLAMA_URL,
            temperature=0.7,
            timeout=300.0,
            num_ctx=8192,
            mcp_servers=mcp_servers,
            max_tool_calls=3,
            tool_call_timeout=30.0
        )
        test_model = OllamaWithMCPModel(config=mcp_config)
        logger.info(f"Test model: {test_model.model_name} with MCP support")

        # Evaluator models
        from models.ollama_model import OllamaModel, OllamaConfig
        evaluator_models = [
            OllamaModel(config=OllamaConfig(
                model_name="mistral:latest",
                base_url=REMOTE_OLLAMA_URL,
                timeout=240.0,
                temperature=0.2
            )),
            OllamaModel(config=OllamaConfig(
                model_name="llama3.2:latest",
                base_url=REMOTE_OLLAMA_URL,
                timeout=240.0,
                temperature=0.2
            ))
        ]
        evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
        logger.info(f"Evaluator models: {[m.model_name for m in evaluator_models]}")

        # Metrics
        mcp_metrics = [
            'tool_usage_accuracy',
            'information_retrieval_quality',
            'contextual_awareness'
        ]
        metrics = MetricFactory.create_metrics_by_names(mcp_metrics)
        logger.info(f"Metrics: {[metric.name for metric in metrics]}")

        # Run benchmark
        runner = BenchmarkRunner(evaluator, metrics)
        benchmark_start_time = datetime.now()
        benchmark_result = await runner.run_benchmark(test_model, dataset)
        runtime_minutes = (datetime.now() - benchmark_start_time).total_seconds() / 60
        logger.info(f"Benchmark completed in {runtime_minutes:.1f} minutes")

        # Save JSON results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = results_dir / f"mcp_benchmark_results_{timestamp}.json"
        benchmark_result.save_to_json_file(str(json_path))
        logger.info(f"Results saved to {json_path}")

        # Generate dashboard
        dashboard_path = results_dir / f"mcp_benchmark_dashboard_{timestamp}.html"
        generate_html_dashboard(benchmark_result, str(dashboard_path))
        logger.info(f"Dashboard generated at {dashboard_path}")

    except FileNotFoundError as e:
        logger.error(f"Dataset not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"MCP benchmark failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
