#!/usr/bin/env python3
"""
RAG Benchmark Runner Script

This script runs benchmark tests for evaluating LLM performance
in Retrieval-Augmented Generation (RAG) scenarios.

RAG evaluation metrics:
- Faithfulness: Does the response stay true to the context?
- Relevance: Does the response answer the question?
- Language Quality: Is the response well-written?
- Grammatical Correctness: Is the grammar correct?
- Overall RAG Score: Combined evaluation
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

from models.ollama_mcp_model import OllamaWithMCPModel, OllamaMCPConfig, MCPServerConfig
from models.ollama_model import OllamaModel, OllamaConfig
from metrics import EvaluatorFactory
from metrics.rag_metrics import get_all_rag_metrics
from benchmark.rag_benchmark_runner import RAGBenchmarkRunner
from dashboard import generate_html_dashboard
from dataset import DatasetLoader

# Server configuration - adjust these for your environment
OLLAMA_BASE_URL = "http://localhost:11434"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_evaluator_models(base_url: str = OLLAMA_BASE_URL):
    """Create judge models for evaluation."""
    return [
        OllamaModel(config=OllamaConfig(
            model_name="llama3.2:latest",
            base_url=base_url,
            timeout=240.0,
            temperature=0.2,
            num_ctx=4096
        )),
    ]


def create_rag_model(model_name: str, base_url: str = OLLAMA_BASE_URL, mcp_servers: list = None):
    """
    Create a model for RAG benchmark.
    
    Can be either a standard model (where context is provided in the prompt)
    or an MCP model (where context is retrieved via tool calls).
    """
    if mcp_servers:
        # MCP-enabled model with tool calling
        mcp_config = OllamaMCPConfig(
            model_name=model_name,
            base_url=base_url,
            temperature=0.7,
            timeout=300.0,
            num_ctx=8192,
            mcp_servers=mcp_servers,
            max_tool_calls=5,
            tool_call_timeout=30.0
        )
        return OllamaWithMCPModel(config=mcp_config)
    else:
        # Standard model - context will be included in prompt
        return OllamaModel(config=OllamaConfig(
            model_name=model_name,
            base_url=base_url,
            timeout=240.0,
            temperature=0.7,
            num_ctx=8192
        ))


async def run_rag_benchmark(
    model_name: str,
    dataset_path: str,
    output_dir: str = "results/rag_benchmark",
    base_url: str = OLLAMA_BASE_URL,
    rag_prompt: str = None
):
    """
    Run RAG benchmark for a model.
    
    Args:
        model_name: Name of the model to test
        dataset_path: Path to the RAG test dataset JSON
        output_dir: Directory for output files
        base_url: Ollama base URL
        rag_prompt: Custom RAG prompt template (uses default if not provided)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Starting RAG benchmark for model: {model_name}")
    logger.info(f"{'='*80}\n")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    logger.info(f"Loading dataset from {dataset_path}")
    dataset = DatasetLoader.from_json_file(dataset_path)
    logger.info(f"Loaded {len(dataset.questions)} questions")
    
    # Create test model
    test_model = create_rag_model(model_name, base_url)
    logger.info(f"Created test model: {model_name}")
    
    # Create evaluator
    evaluator_models = create_evaluator_models(base_url)
    evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
    logger.info(f"Created evaluator with {len(evaluator_models)} model(s)")
    
    # Get RAG metrics
    metrics = get_all_rag_metrics()
    logger.info(f"Using {len(metrics)} RAG metrics: {[m.name for m in metrics]}")
    
    # Create and run benchmark (runner handles prompt injection)
    runner = RAGBenchmarkRunner(evaluator, metrics, rag_prompt=rag_prompt)
    benchmark_result = await runner.run_benchmark(test_model, dataset)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model_name = model_name.replace(":", "_").replace("/", "_")
    
    # Save JSON results
    json_path = output_path / f"rag_{safe_model_name}_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json.loads(benchmark_result.to_json()), f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON results to {json_path}")
    
    # Generate HTML dashboard
    html_path = output_path / f"rag_{safe_model_name}_{timestamp}.html"
    html_content = generate_rag_html_report(benchmark_result, model_name, dataset)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info(f"Saved HTML report to {html_path}")
    
    # Print summary
    print_benchmark_summary(benchmark_result)
    
    return benchmark_result


def generate_rag_html_report(result, model_name: str, dataset) -> str:
    """Generate a detailed HTML report for RAG benchmark results."""
    
    # Calculate metric summaries
    metric_data = result.metadata.get('metric_summaries', {})
    
    metrics_html = ""
    for metric_name, stats in metric_data.items():
        color = get_score_color(stats['average'])
        metrics_html += f"""
        <div class="metric-card">
            <h3>{format_metric_name(metric_name)}</h3>
            <div class="score" style="background-color: {color};">{stats['average']:.2f}/5</div>
            <div class="stats">
                <span>Min: {stats['min']:.1f}</span>
                <span>Max: {stats['max']:.1f}</span>
            </div>
        </div>
        """
    
    # Build questions HTML
    questions_html = ""
    for i, pe in enumerate(result.prompt_evaluations):
        eval_details = ""
        for ev in pe.evaluations:
            color = get_score_color(ev.score)
            eval_details += f"""
            <div class="eval-item">
                <span class="metric-name">{format_metric_name(ev.metric_name)}</span>
                <span class="score-badge" style="background-color: {color};">{ev.score:.1f}</span>
                <p class="rationale">{ev.rationale[:200]}...</p>
            </div>
            """
        
        questions_html += f"""
        <div class="question-card">
            <h4>Question {i+1}</h4>
            <div class="query"><strong>Query:</strong> {pe.prompt[:200]}...</div>
            <div class="response"><strong>Response:</strong> {pe.response[:300]}...</div>
            <div class="evaluations">
                {eval_details}
            </div>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RAG Benchmark Results - {model_name}</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ color: #1976d2; margin-bottom: 20px; }}
            h2 {{ color: #333; margin: 30px 0 15px; }}
            .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
            .summary-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
            .summary-card h3 {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
            .summary-card .value {{ font-size: 32px; font-weight: bold; color: #1976d2; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-bottom: 30px; }}
            .metric-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
            .metric-card h3 {{ color: #333; font-size: 16px; margin-bottom: 10px; }}
            .metric-card .score {{ font-size: 28px; font-weight: bold; color: white; padding: 10px; border-radius: 8px; }}
            .metric-card .stats {{ margin-top: 10px; color: #666; font-size: 12px; }}
            .metric-card .stats span {{ margin: 0 5px; }}
            .question-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 15px; }}
            .question-card h4 {{ color: #1976d2; margin-bottom: 10px; }}
            .query, .response {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 4px; font-size: 14px; }}
            .evaluations {{ margin-top: 15px; }}
            .eval-item {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px; }}
            .metric-name {{ font-weight: bold; min-width: 150px; }}
            .score-badge {{ color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; }}
            .rationale {{ width: 100%; color: #666; font-size: 13px; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 RAG Benchmark Results</h1>
            
            <div class="summary">
                <div class="summary-card">
                    <h3>Model</h3>
                    <div class="value" style="font-size: 18px;">{model_name}</div>
                </div>
                <div class="summary-card">
                    <h3>Overall Score</h3>
                    <div class="value">{result.overall_score:.2f}/5</div>
                </div>
                <div class="summary-card">
                    <h3>Questions</h3>
                    <div class="value">{len(result.prompt_evaluations)}</div>
                </div>
                <div class="summary-card">
                    <h3>Metrics</h3>
                    <div class="value">{len(metric_data)}</div>
                </div>
            </div>
            
            <h2>📊 RAG Quality Metrics</h2>
            <div class="metrics-grid">
                {metrics_html}
            </div>
            
            <h2>📝 Question Details</h2>
            {questions_html}
        </div>
    </body>
    </html>
    """
    
    return html


def format_metric_name(name: str) -> str:
    """Format metric name for display."""
    if not name:
        return "Unknown"
    return name.replace('_', ' ').title()


def get_score_color(score: float) -> str:
    """Get color based on score (1-5 scale)."""
    if score >= 4:
        return "#4caf50"  # Green
    elif score >= 3:
        return "#2196f3"  # Blue
    elif score >= 2:
        return "#ff9800"  # Orange
    else:
        return "#f44336"  # Red


def print_benchmark_summary(result):
    """Print a summary of benchmark results to console."""
    print("\n" + "="*60)
    print("RAG BENCHMARK SUMMARY")
    print("="*60)
    
    print(f"\nOverall Score: {result.overall_score:.2f}/5")
    print(f"Questions Evaluated: {len(result.prompt_evaluations)}")
    
    metric_summaries = result.metadata.get('metric_summaries', {})
    if metric_summaries:
        print("\nMetric Scores:")
        print("-"*40)
        for metric_name, stats in metric_summaries.items():
            print(f"  {format_metric_name(metric_name):30} {stats['average']:.2f}/5")
    
    print("\n" + "="*60 + "\n")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RAG Benchmark")
    parser.add_argument(
        "--model", 
        type=str, 
        default="llama3.2:latest",
        help="Model name to benchmark"
    )
    parser.add_argument(
        "--dataset", 
        type=str, 
        default="rag_test_dataset.json",
        help="Path to RAG test dataset JSON"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="results/rag_benchmark",
        help="Output directory for results"
    )
    parser.add_argument(
        "--base-url", 
        type=str, 
        default=OLLAMA_BASE_URL,
        help="Ollama base URL"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Custom RAG prompt template (must include {context} and {query} placeholders)"
    )
    
    args = parser.parse_args()
    
    await run_rag_benchmark(
        model_name=args.model,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        base_url=args.base_url,
        rag_prompt=args.prompt
    )


if __name__ == "__main__":
    asyncio.run(main())
