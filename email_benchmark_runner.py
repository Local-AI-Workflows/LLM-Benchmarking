#!/usr/bin/env python3
"""
Email Response Quality Benchmark Runner

This script runs a comprehensive benchmark test for evaluating LLM performance
on email response quality using custom metrics and a specialized dataset.
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


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the email response quality benchmark."""
    
    print("🚀 Starting Email Response Quality Benchmark")
    print("=" * 60)
    
    # Create results directory
    results_dir = Path("email_benchmark_results")
    results_dir.mkdir(exist_ok=True)
    
    try:
        # 1. Load the email response dataset
        print("\n📧 Loading Email Response Dataset...")
        dataset = DatasetLoader.load_from_file("email_response_dataset.json")
        
        print(f"✅ Loaded dataset: {dataset.name}")
        print(f"   Description: {dataset.description}")
        print(f"   Number of email scenarios: {len(dataset)}")
        
        # Display dataset statistics
        stats = dataset.get_statistics()
        print(f"   Email types: {set(q.get_metadata('email_type') for q in dataset.questions if q.get_metadata('email_type'))}")
        print(f"   Difficulty levels: {set(q.get_metadata('difficulty') for q in dataset.questions if q.get_metadata('difficulty'))}")
        
        # 2. Initialize the LLM model to be tested with optimized settings
        print("\n🤖 Initializing Test Model...")
        test_model = OllamaModel(config=OllamaConfig(
            model_name="llama3.2:latest",
            temperature=0.7,  # Slight creativity for natural responses
            timeout=180.0,    # 3 minutes timeout for generation
            num_ctx=4096      # Larger context window for longer emails
        ))
        print(f"✅ Test model: {test_model.model_name}")
        
        # 3. Initialize evaluator models with robust configuration
        print("\n⚖️ Initializing Evaluator Models...")
        evaluator_models = [
            OllamaModel(config=OllamaConfig(
                model_name="deepseek-r1:1.5b",
                timeout=180.0,
                temperature=0.3  # Lower temperature for more consistent evaluation
            )),
            OllamaModel(config=OllamaConfig(
                model_name="gemma3:1b",
                timeout=180.0,
                temperature=0.3
            )),
            OllamaModel(config=OllamaConfig(
                model_name="llama3.2:latest",
                timeout=180.0,
                temperature=0.3
            ))
        ]
        evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
        print(f"✅ Evaluator models: {[model.model_name for model in evaluator_models]}")
        
        # 4. Initialize email-specific metrics
        print("\n📊 Initializing Email-Specific Metrics...")
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
        print("\n🏃 Running Email Response Benchmark...")
        print("⏱️  This will take approximately 15-20 minutes for all 20 scenarios...")
        print("💡 The process includes:")
        print("   1. Generating email responses (3-5 min)")
        print("   2. Evaluating with multiple metrics (10-15 min)")
        print("   3. Creating visualizations and dashboard (1-2 min)")
        
        runner = BenchmarkRunner(evaluator, metrics)
        
        print(f"\nProcessing {len(dataset)} email scenarios...")
        benchmark_result = await runner.run_benchmark(test_model, dataset)
        
        print("✅ Benchmark completed successfully!")
        
        # 6. Save results to JSON
        print("\n💾 Saving Results...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON results
        json_filename = f"email_benchmark_results_{timestamp}.json"
        json_path = results_dir / json_filename
        benchmark_result.save_to_json_file(str(json_path))
        print(f"✅ Results saved to: {json_path}")
        
        # 7. Generate visualizations
        print("\n📊 Generating Visualizations...")
        visualizer = EvaluationVisualizer()
        
        # Generate various charts
        viz_dir = results_dir / f"visualizations_{timestamp}"
        viz_dir.mkdir(exist_ok=True)
        
        try:
            # Overall performance chart
            overall_chart = visualizer.create_overall_performance_chart(benchmark_result)
            overall_chart.savefig(viz_dir / "overall_performance.png", dpi=300, bbox_inches='tight')
            print("✅ Overall performance chart saved")
            
            # Metrics comparison chart
            metrics_chart = visualizer.create_metrics_comparison_chart(benchmark_result)
            metrics_chart.savefig(viz_dir / "metrics_comparison.png", dpi=300, bbox_inches='tight')
            print("✅ Metrics comparison chart saved")
            
            # Performance by question chart
            questions_chart = visualizer.create_performance_by_question_chart(benchmark_result)
            questions_chart.savefig(viz_dir / "performance_by_question.png", dpi=300, bbox_inches='tight')
            print("✅ Performance by question chart saved")
            
        except Exception as e:
            print(f"⚠️ Warning: Some visualizations failed to generate: {e}")
        
        # 8. Generate interactive HTML dashboard
        print("\n🌐 Generating Interactive HTML Dashboard...")
        dashboard_filename = f"email_benchmark_dashboard_{timestamp}.html"
        dashboard_path = results_dir / dashboard_filename
        
        generated_path = generate_html_dashboard(benchmark_result, str(dashboard_path))
        print(f"✅ Interactive dashboard generated: {generated_path}")
        
        # 9. Print summary statistics
        print("\n📈 Benchmark Results Summary")
        print("=" * 40)
        
        # Get summary statistics
        stats = benchmark_result.get_summary_statistics()
        
        print(f"Total email scenarios tested: {stats['num_prompts']}")
        print(f"Total evaluations performed: {len(benchmark_result.prompt_evaluations) * len(email_metrics)}")
        print(f"Overall average score: {stats['overall_average']:.2f}/10")
        
        print("\nAverage scores by metric:")
        for metric_name, avg_score in stats['average_scores'].items():
            print(f"  • {metric_name.replace('_', ' ').title()}: {avg_score:.2f}/10")
        
        # Performance by email type
        print("\nPerformance by email type:")
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
        print("\nPerformance by difficulty level:")
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
        print("\nTop performing email scenarios:")
        prompt_scores = []
        for eval_result in benchmark_result.prompt_evaluations:
            prompt_avg = sum(e.score for e in eval_result.evaluations) / len(eval_result.evaluations)
            # Find the question ID
            question_id = "unknown"
            for question in dataset.questions:
                if question.get_full_prompt() == eval_result.prompt:
                    question_id = question.id
                    break
            prompt_scores.append((question_id, prompt_avg))
        
        # Sort by score and show top 3
        prompt_scores.sort(key=lambda x: x[1], reverse=True)
        for i, (question_id, score) in enumerate(prompt_scores[:3], 1):
            print(f"  {i}. {question_id}: {score:.2f}/10")
        
        # 10. Provide file locations and next steps
        print(f"\n📁 Results saved to: {results_dir.absolute()}")
        print("Files generated:")
        print(f"  • JSON results: {json_filename}")
        print(f"  • HTML dashboard: {dashboard_filename}")
        print(f"  • Visualizations: visualizations_{timestamp}/")
        
        print(f"\n🎉 Email Response Quality Benchmark completed successfully!")
        print(f"🌐 Open {dashboard_path.absolute()} in your browser to view the interactive dashboard")
        print(f"\n💡 Next steps:")
        print(f"   • Review the dashboard for detailed analysis")
        print(f"   • Check email responses that scored highest/lowest")
        print(f"   • Consider adjusting model parameters based on results")
        print(f"   • Add more scenarios or metrics as needed")
        
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find email dataset file: {e}")
        print("Please ensure 'email_response_dataset.json' exists in the current directory")
        return 1
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        print(f"❌ Benchmark failed: {e}")
        print(f"\n🔧 Troubleshooting tips:")
        print(f"   • Check that Ollama is running: curl http://localhost:11434/api/version")
        print(f"   • Verify models are available: ollama list")
        print(f"   • Try reducing the number of scenarios in demo_email_benchmark.py first")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 