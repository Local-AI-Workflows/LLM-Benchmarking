#!/usr/bin/env python3
"""
Email Response Quality Benchmark Runner - Remote Server Version

Runs a benchmark for evaluating LLM performance on email response quality using
a remote Ollama server with more powerful models.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from models.ollama_model import OllamaModel, OllamaConfig
from metrics import MetricFactory, EvaluatorFactory
from benchmark.runner import BenchmarkRunner
from visualizations.evaluation_visualizer import EvaluationVisualizer
from dashboard import generate_html_dashboard
from dataset import DatasetLoader

REMOTE_OLLAMA_URL = "http://ollama.ios.htwg-konstanz.de:11434"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run the email response quality benchmark on a remote server."""
    logger.info("Starting Email Response Quality Benchmark")

    results_dir = Path(".doc/benchmark_results/email_benchmark_results")
    results_dir.mkdir(exist_ok=True)

    try:
        # Load dataset
        dataset = DatasetLoader.load_from_file(".doc/test_data/email_response_dataset.json")
        logger.info("Loaded dataset '%s' (%d scenarios)", dataset.name, len(dataset))

        # Initialize test model
        test_model = OllamaModel(config=OllamaConfig(
            model_name="mixtral:latest",
            base_url=REMOTE_OLLAMA_URL,
            temperature=0.7,
            timeout=300.0,
            num_ctx=8192,
            top_p=0.9,
            top_k=40
        ))
        logger.info("Using test model: %s", test_model.model_name)

        # Initialize evaluator models
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
        logger.info("Evaluator models: %s", [m.model_name for m in evaluator_models])

        # Initialize metrics
        email_metrics = [
            'email_professionalism',
            'email_responsiveness',
            'email_clarity',
            'email_empathy'
        ]
        metrics = MetricFactory.create_metrics_by_names(email_metrics)
        logger.info("Email metrics loaded: %s", [m.name for m in metrics])

        # Run benchmark
        logger.info("Running benchmark...")
        runner = BenchmarkRunner(evaluator, metrics)
        benchmark_start_time = datetime.now()
        benchmark_result = await runner.run_benchmark(test_model, dataset)
        benchmark_end_time = datetime.now()
        logger.info("Benchmark completed in %.1f minutes",
                    (benchmark_end_time - benchmark_start_time).total_seconds() / 60)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"email_benchmark_results_remote_{timestamp}.json"
        json_path = results_dir / json_filename
        benchmark_result.save_to_json_file(str(json_path))
        logger.info("Results saved to: %s", json_path)

        # Generate visualizations
        viz_dir = results_dir / f"visualizations_remote_{timestamp}"
        viz_dir.mkdir(exist_ok=True)
        visualizer = EvaluationVisualizer()
        try:
            visualizer.create_overall_performance_chart(benchmark_result)\
                .savefig(viz_dir / "overall_performance.png", dpi=300, bbox_inches='tight')
            visualizer.create_metrics_comparison_chart(benchmark_result)\
                .savefig(viz_dir / "metrics_comparison.png", dpi=300, bbox_inches='tight')
            visualizer.create_performance_by_question_chart(benchmark_result)\
                .savefig(viz_dir / "performance_by_question.png", dpi=300, bbox_inches='tight')
            logger.info("Visualizations generated in %s", viz_dir)
        except Exception as e:
            logger.warning("Some visualizations failed to generate: %s", e)

        # Generate dashboard
        dashboard_filename = f"email_benchmark_dashboard_remote_{timestamp}.html"
        dashboard_path = results_dir / dashboard_filename
        generate_html_dashboard(benchmark_result, str(dashboard_path))
        logger.info("Dashboard generated: %s", dashboard_path)

        # Summary
        stats = benchmark_result.get_summary_statistics()
        logger.info("Total scenarios tested: %d", stats['num_prompts'])
        logger.info("Overall average score: %.2f/10", stats['overall_average'])

    except FileNotFoundError as e:
        logger.error("Could not find dataset file: %s", e)
        return 1
    except Exception as e:
        logger.error("Benchmark failed: %s", e, exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
