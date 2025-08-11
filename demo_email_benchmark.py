#!/usr/bin/env python3
"""
Email Benchmark Demo Script

This script demonstrates the email response quality benchmark with a small
subset of scenarios for quick testing and demonstration purposes.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from models.ollama_model import OllamaModel, OllamaConfig
from metrics import MetricFactory, EvaluatorFactory
from metrics.responses import BenchmarkResult
from benchmark.runner import BenchmarkRunner
from dashboard import generate_html_dashboard
from dataset import DatasetLoader, Dataset

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_email_benchmark():
    """Demonstrate the email benchmark with a small subset of scenarios."""
    
    print("🚀 Email Response Quality Benchmark - Demo")
    print("=" * 50)
    
    try:
        # 1. Load just the first 3 scenarios for demo
        print("\n📧 Loading Email Dataset (Demo Subset)...")
        full_dataset = DatasetLoader.load_from_file("email_response_dataset.json")
        
        # Create a smaller demo dataset with just 3 scenarios
        demo_questions = full_dataset.questions[:3]
        demo_dataset = Dataset(
            questions=demo_questions,
            name="Email Benchmark Demo",
            description="Demo with 3 email scenarios for testing"
        )
        
        print(f"✅ Demo dataset: {len(demo_dataset)} scenarios")
        for i, q in enumerate(demo_dataset.questions, 1):
            print(f"   {i}. {q.id}: {q.get_metadata('scenario', 'N/A')} ({q.get_metadata('difficulty', 'N/A')})")
        
        # 2. Initialize models with increased timeout
        print("\n🤖 Initializing Models...")
        test_model = OllamaModel(config=OllamaConfig(
            model_name="llama3.2:latest",
            temperature=0.7,
            timeout=120.0  # Increased timeout to 2 minutes
        ))
        
        # Use fewer evaluator models for demo
        evaluator_models = [
            OllamaModel(config=OllamaConfig(
                model_name="llama3.2:latest",
                timeout=120.0  # Increased timeout for evaluators too
            ))
        ]
        evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
        
        print(f"✅ Test model: {test_model.model_name}")
        print(f"✅ Evaluator models: {[m.model_name for m in evaluator_models]}")
        
        # 3. Initialize email metrics
        print("\n📊 Initializing Email Metrics...")
        email_metrics = [
            'email_professionalism',
            'email_responsiveness'
        ]
        
        metrics = MetricFactory.create_metrics_by_names(email_metrics)
        print(f"✅ Using {len(metrics)} metrics for demo:")
        for metric in metrics:
            print(f"   • {metric.name}")
        
        # 4. Run demo benchmark
        print("\n🏃 Running Demo Benchmark...")
        runner = BenchmarkRunner(evaluator, metrics)
        
        print("Generating responses and evaluations...")
        print("Note: This may take a few minutes as we generate and evaluate responses...")
        benchmark_result = await runner.run_benchmark(test_model, demo_dataset)
        
        print("✅ Demo benchmark completed!")
        
        # 5. Show results
        print("\n📈 Demo Results Summary")
        print("=" * 30)
        
        stats = benchmark_result.get_summary_statistics()
        print(f"Scenarios tested: {stats['num_prompts']}")
        print(f"Overall average: {stats['overall_average']:.2f}/10")
        
        print("\nScores by metric:")
        for metric_name, avg_score in stats['average_scores'].items():
            print(f"  • {metric_name.replace('_', ' ').title()}: {avg_score:.2f}/10")
        
        print("\nSample evaluation details:")
        print("-" * 30)
        
        # Show details for first scenario
        first_eval = benchmark_result.prompt_evaluations[0]
        print(f"Scenario: {demo_questions[0].id}")
        print(f"Original message: {demo_questions[0].text[:100]}...")
        print(f"Generated response: {first_eval.response[:150]}...")
        
        for eval_result in first_eval.evaluations:
            print(f"\n{eval_result.metric_name.replace('_', ' ').title()}:")
            print(f"  Score: {eval_result.score:.1f}/10")
            print(f"  Rationale: {eval_result.rationale[:200]}...")
        
        # 6. Save demo results
        print(f"\n💾 Saving Demo Results...")
        results_dir = Path("demo_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_path = results_dir / f"demo_results_{timestamp}.json"
        benchmark_result.save_to_json_file(str(json_path))
        print(f"✅ Results saved: {json_path}")
        
        # Generate HTML dashboard
        dashboard_path = results_dir / f"demo_dashboard_{timestamp}.html"
        generate_html_dashboard(benchmark_result, str(dashboard_path))
        print(f"✅ Dashboard saved: {dashboard_path}")
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"🌐 Open {dashboard_path.absolute()} to view the dashboard")
        
        return benchmark_result
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"❌ Demo failed: {e}")
        return None


async def main():
    """Main function."""
    result = await demo_email_benchmark()
    if result:
        print("\n✅ Demo completed successfully!")
        return 0
    else:
        print("\n❌ Demo failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 