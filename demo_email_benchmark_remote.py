#!/usr/bin/env python3
"""
Email Benchmark Demo Script - Remote Server Version

This script demonstrates the email response quality benchmark with a small
subset of scenarios using the remote server with the updated configuration.
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

# Remote server configuration
REMOTE_OLLAMA_URL = "http://ollama.ios.htwg-konstanz.de:11434"


async def demo_email_benchmark():
    """Demonstrate the email benchmark with a small subset of scenarios using remote server."""
    
    print("🚀 Email Response Quality Benchmark - Remote Demo")
    print("=" * 55)
    print(f"🌐 Using remote Ollama server: {REMOTE_OLLAMA_URL}")
    
    try:
        # 1. Load just the first 3 scenarios for demo
        print("\n📧 Loading Email Dataset (Demo Subset)...")
        full_dataset = DatasetLoader.load_from_file("email_response_dataset.json")
        
        # Create a smaller demo dataset with just 3 scenarios
        demo_questions = full_dataset.questions[:3]
        demo_dataset = Dataset(
            questions=demo_questions,
            name="Email Benchmark Remote Demo",
            description="Demo with 3 email scenarios using remote server"
        )
        
        print(f"✅ Demo dataset: {len(demo_dataset)} scenarios")
        for i, q in enumerate(demo_dataset.questions, 1):
            print(f"   {i}. {q.id}: {q.get_metadata('scenario', 'N/A')} ({q.get_metadata('difficulty', 'N/A')})")
        
        # 2. Initialize models with remote server
        print("\n🤖 Initializing Test Model (Mixtral)...")
        test_model = OllamaModel(config=OllamaConfig(
            model_name="mixtral:latest",
            base_url=REMOTE_OLLAMA_URL,
            temperature=0.7,
            timeout=180.0
        ))
        
        # Use only Mistral and Llama3.2 as evaluators (no DeepSeek)
        print("\n⚖️ Initializing Evaluator Models...")
        evaluator_models = [
            OllamaModel(config=OllamaConfig(
                model_name="mistral:latest",
                base_url=REMOTE_OLLAMA_URL,
                timeout=180.0,
                temperature=0.2
            )),
            OllamaModel(config=OllamaConfig(
                model_name="llama3.2:latest",
                base_url=REMOTE_OLLAMA_URL,
                timeout=180.0,
                temperature=0.2
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
        print("\n🏃 Running Remote Demo Benchmark...")
        runner = BenchmarkRunner(evaluator, metrics)
        
        print("Generating responses and evaluations...")
        print("Note: This will test the updated HTML dashboard features...")
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
        
        # 6. Save demo results and test updated dashboard
        print(f"\n💾 Saving Demo Results...")
        results_dir = Path("demo_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_path = results_dir / f"demo_remote_results_{timestamp}.json"
        benchmark_result.save_to_json_file(str(json_path))
        print(f"✅ Results saved: {json_path}")
        
        # Generate HTML dashboard with updated features
        dashboard_path = results_dir / f"demo_remote_dashboard_{timestamp}.html"
        generate_html_dashboard(benchmark_result, str(dashboard_path))
        print(f"✅ Updated dashboard saved: {dashboard_path}")
        
        print(f"\n🎉 Remote demo completed successfully!")
        print(f"🌐 Open {dashboard_path.absolute()} to view the UPDATED dashboard")
        print(f"\n🔧 Dashboard improvements:")
        print(f"   • Correlation matrix labels are now rotated for better readability")
        print(f"   • Detailed analysis tab now includes the model responses")
        print(f"   • No DeepSeek evaluator (as requested)")
        
        return benchmark_result
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"❌ Demo failed: {e}")
        return None


async def main():
    """Main function."""
    result = await demo_email_benchmark()
    if result:
        print("\n✅ Remote demo completed successfully!")
        return 0
    else:
        print("\n❌ Remote demo failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 