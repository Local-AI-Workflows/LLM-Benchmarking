#!/usr/bin/env python3
"""
Email Response Quality Benchmark Runner - Remote Server Version

This script runs a comprehensive benchmark test for evaluating LLM performance
on email response quality using the remote Ollama server with more powerful models.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from models.ollama_model import OllamaModel, OllamaConfig
from metrics import MetricFactory, EvaluatorFactory
from metrics.responses import BenchmarkResult
from benchmark.runner import BenchmarkRunner
from visualizations.evaluation_visualizer import EvaluationVisualizer
from dashboard import generate_html_dashboard
from dataset import DatasetLoader


# Remote server configuration
REMOTE_OLLAMA_URL = "http://ollama.ios.htwg-konstanz.de:11434"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the email response quality benchmark on remote server."""
    
    print("Starting Email Response Quality Benchmark")

    # Create results directory
    results_dir = Path(".doc/benchmark_results/email_benchmark_results")
    results_dir.mkdir(exist_ok=True)
    
    try:
        # 1. Load the email response dataset
        print("\nLoading Email Response Dataset...")
        dataset = DatasetLoader.load_from_file(".doc/test_data/email_response_dataset.json")
        
        print(f"Loaded dataset: {dataset.name}")
        print(f"Description: {dataset.description}")
        print(f"Number of scenarios: {len(dataset)}")
        
        # Display dataset statistics
        stats = dataset.get_statistics()
        print(f"   Email types: {set(q.get_metadata('email_type') for q in dataset.questions if q.get_metadata('email_type'))}")
        print(f"   Difficulty levels: {set(q.get_metadata('difficulty') for q in dataset.questions if q.get_metadata('difficulty'))}")
        
        # 2. Initialize the test model - using the most powerful model for generation
        print("\nInitializing Test Model (Mixtral 46.7B)...")
        test_model = OllamaModel(config=OllamaConfig(
            model_name="mixtral:latest",
            base_url=REMOTE_OLLAMA_URL,
            temperature=0.7,      # Balanced creativity for natural email responses
            timeout=300.0,        # 5 minutes timeout for the large model
            num_ctx=8192,         # Large context window for complex emails
            top_p=0.9,            # Good balance for quality generation
            top_k=40              # Reasonable diversity
        ))
        print(f"✅ Test model: {test_model.model_name} (46.7B parameters)")
        print(f"   Server: {REMOTE_OLLAMA_URL}")
        
        # 3. Initialize evaluator models - diverse set excluding the test model
        print("\nInitializing Evaluator Models...")
        evaluator_models = [
            OllamaModel(config=OllamaConfig(
                model_name="mistral:latest",
                base_url=REMOTE_OLLAMA_URL,
                timeout=240.0,    # 4 minutes for evaluation
                temperature=0.2   # Lower temperature for consistent evaluation
            )),
            OllamaModel(config=OllamaConfig(
                model_name="llama3.2:latest",
                base_url=REMOTE_OLLAMA_URL,
                timeout=240.0,
                temperature=0.2
            ))
        ]
        evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
        print(f"Evaluator models: {[model.model_name for model in evaluator_models]}")
        print(f"   • Mistral 7.2B (Q4_0)")
        print(f"   • Llama3.2 3.2B (Q4_K_M)")
        
        # 4. Initialize email-specific metrics
        print("\nInitializing Email-Specific Metrics...")
        email_metrics = [
            'email_professionalism',
            'email_responsiveness', 
            'email_clarity',
            'email_empathy'
        ]
        
        metrics = MetricFactory.create_metrics_by_names(email_metrics)
        print(f"✅ Email metrics loaded: {[metric.name for metric in metrics]}")
        
        for metric in metrics:
            print(f"   • {metric.name}: {metric.description}")
        
        # 5. Create and run benchmark
        print("\nRunning Email Response Benchmark...")
        print("Expected runtime with remote server: 10-15 minutes")
        print("💡 Process breakdown:")
        print("   1. Generating 20 email responses with Mixtral (5-8 min)")
        print("   2. Evaluating responses with 3 models × 4 metrics (5-7 min)")
        print("   3. Creating visualizations and dashboard (1-2 min)")
        print("\nStarting benchmark execution...")
        
        runner = BenchmarkRunner(evaluator, metrics)
        
        benchmark_start_time = datetime.now()
        benchmark_result = await runner.run_benchmark(test_model, dataset)
        benchmark_end_time = datetime.now()
        
        runtime_minutes = (benchmark_end_time - benchmark_start_time).total_seconds() / 60
        print(f"Benchmark completed successfully in {runtime_minutes:.1f} minutes!")
        
        # 6. Save results to JSON
        print("\nSaving Results...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON results
        json_filename = f"email_benchmark_results_remote_{timestamp}.json"
        json_path = results_dir / json_filename
        benchmark_result.save_to_json_file(str(json_path))
        print(f"Results saved to: {json_path}")
        
        # 7. Generate visualizations
        print("\nGenerating Visualizations...")
        visualizer = EvaluationVisualizer()
        
        # Generate various charts
        viz_dir = results_dir / f"visualizations_remote_{timestamp}"
        viz_dir.mkdir(exist_ok=True)
        
        try:
            # Overall performance chart
            overall_chart = visualizer.create_overall_performance_chart(benchmark_result)
            overall_chart.savefig(viz_dir / "overall_performance.png", dpi=300, bbox_inches='tight')
            print("Overall performance chart saved")
            
            # Metrics comparison chart
            metrics_chart = visualizer.create_metrics_comparison_chart(benchmark_result)
            metrics_chart.savefig(viz_dir / "metrics_comparison.png", dpi=300, bbox_inches='tight')
            print("Metrics comparison chart saved")
            
            # Performance by question chart
            questions_chart = visualizer.create_performance_by_question_chart(benchmark_result)
            questions_chart.savefig(viz_dir / "performance_by_question.png", dpi=300, bbox_inches='tight')
            print("Performance by question chart saved")
            
        except Exception as e:
            print(f"Warning: Some visualizations failed to generate: {e}")
        
        # 8. Generate interactive HTML dashboard
        print("\nGenerating Interactive HTML Dashboard...")
        dashboard_filename = f"email_benchmark_dashboard_remote_{timestamp}.html"
        dashboard_path = results_dir / dashboard_filename
        
        generated_path = generate_html_dashboard(benchmark_result, str(dashboard_path))
        print(f"Dashboard generated: {generated_path}")
        
        # 9. Print comprehensive summary statistics
        print("\nBenchmark Results Summary")

        # Get summary statistics
        stats = benchmark_result.get_summary_statistics()
        
        print(f"\nResults Overview:")
        print(f"Total email scenarios tested: {stats['num_prompts']}")
        print(f"Total evaluations performed: {len(benchmark_result.prompt_evaluations) * len(email_metrics)}")
        print(f"Overall average score: {stats['overall_average']:.2f}/10")
        
        print(f"\nAverage scores by metric:")
        for metric_name, avg_score in stats['average_scores'].items():
            print(f"  • {metric_name.replace('_', ' ').title()}: {avg_score:.2f}/10")
        
        # Performance by email type
        print(f"\nPerformance by email type:")
        email_type_scores = {}
        for eval_result in benchmark_result.prompt_evaluations:
            # Find the question for this prompt to get metadata
            for question in dataset.questions:
                if question.get_full_prompt() == eval_result.prompt:
                    email_type = question.get_metadata('email_type', 'unknown')
                    if email_type not in email_type_scores:
                        email_type_scores[email_type] = []
                    
                    # Average across all metrics for this prompt
                    prompt_avg = sum(e.score for e in eval_result.evaluations) / len(eval_result.evaluations)
                    email_type_scores[email_type].append(prompt_avg)
                    break
        
        for email_type, scores in email_type_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"  • {email_type.title()}: {avg_score:.2f}/10 ({len(scores)} scenarios)")
        
        # Performance by difficulty
        print(f"\nPerformance by difficulty level:")
        difficulty_scores = {}
        for eval_result in benchmark_result.prompt_evaluations:
            for question in dataset.questions:
                if question.get_full_prompt() == eval_result.prompt:
                    difficulty = question.get_metadata('difficulty', 'unknown')
                    if difficulty not in difficulty_scores:
                        difficulty_scores[difficulty] = []
                    
                    prompt_avg = sum(e.score for e in eval_result.evaluations) / len(eval_result.evaluations)
                    difficulty_scores[difficulty].append(prompt_avg)
                    break
        
        for difficulty, scores in difficulty_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"  • {difficulty.title()}: {avg_score:.2f}/10 ({len(scores)} scenarios)")
        
        # Show top performing scenarios
        print(f"\nTop performing email scenarios:")
        prompt_scores = []
        for eval_result in benchmark_result.prompt_evaluations:
            prompt_avg = sum(e.score for e in eval_result.evaluations) / len(eval_result.evaluations)
            # Find the question ID and scenario
            question_id = "unknown"
            scenario = "unknown"
            for question in dataset.questions:
                if question.get_full_prompt() == eval_result.prompt:
                    question_id = question.id
                    scenario = question.get_metadata('scenario', 'unknown')
                    break
            prompt_scores.append((question_id, scenario, prompt_avg))
        
        # Sort by score and show top 5
        prompt_scores.sort(key=lambda x: x[2], reverse=True)
        for i, (question_id, scenario, score) in enumerate(prompt_scores[:5], 1):
            print(f"  {i}. {question_id} ({scenario}): {score:.2f}/10")
        
        # Show challenging scenarios
        print(f"\nMost challenging scenarios:")
        for i, (question_id, scenario, score) in enumerate(prompt_scores[-3:], 1):
            print(f"  {i}. {question_id} ({scenario}): {score:.2f}/10")
        
        # 10. Provide comprehensive next steps
        print(f"\nResults saved to: {results_dir.absolute()}")
        print("Files generated:")
        print(f"  • JSON results: {json_filename}")
        print(f"  • HTML dashboard: {dashboard_filename}")
        print(f"  • Visualizations: visualizations_remote_{timestamp}/")
        
        print(f"\nEmail Response Quality Benchmark completed successfully!")
        print(f"Open {dashboard_path.absolute()} in your browser to view the interactive dashboard")
        

    except FileNotFoundError as e:
        print(f"❌ Error: Could not find email dataset file: {e}")
        print("Please ensure 'email_response_dataset.json' exists in the current directory")
        return 1
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 