#!/usr/bin/env python3
"""
MCP Tool Usage Demo Script

This script demonstrates the MCP tool usage benchmark with a single test scenario.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from models.ollama_mcp_model import OllamaWithMCPModel, OllamaMCPConfig, MCPServerConfig
from metrics import MetricFactory, EvaluatorFactory
from metrics.responses import BenchmarkResult
from benchmark.runner import BenchmarkRunner
from dashboard import generate_html_dashboard
from dataset import DatasetLoader, Dataset

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MCP Server configuration
REMOTE_OLLAMA_URL = "http://ollama.ios.htwg-konstanz.de:11434"
MCP_WEATHER_URL = "http://ollama.ios.htwg-konstanz.de:8007"
MCP_MENSA_URL = "http://ollama.ios.htwg-konstanz.de:8008"


async def demo_mcp_benchmark():
    """Demonstrate the MCP benchmark with a single scenario."""
    
    print("🚀 MCP Tool Usage Benchmark - Demo")
    print("=" * 40)
    print(f"🌐 Remote Ollama: {REMOTE_OLLAMA_URL}")
    print(f"🌤️  Weather MCP: {MCP_WEATHER_URL}")
    
    try:
        # 1. Load just the first scenario for demo
        print("\n🔧 Loading MCP Demo Dataset...")
        full_dataset = DatasetLoader.load_from_file("mcp_test_dataset.json")
        
        # Create a demo dataset with just the first scenario  
        demo_questions = full_dataset.questions[:1]
        demo_dataset = Dataset(
            questions=demo_questions,
            name="MCP Benchmark Demo",
            description="Demo with 1 MCP scenario"
        )
        
        print(f"✅ Demo dataset: {len(demo_dataset)} scenario")
        for q in demo_dataset.questions:
            print(f"   • {q.id}: {q.get_metadata('scenario', 'N/A')} ({q.get_metadata('difficulty', 'N/A')})")
        
        # 2. Initialize MCP-enabled model
        print("\n🤖 Initializing MCP-Enabled Model...")
        
        mcp_servers = [
            MCPServerConfig(
                name="weather",
                url=MCP_WEATHER_URL,
                description="Get current weather and forecasts",
                available_tools=["get_weather", "get_forecast"]
            )
        ]
        
        mcp_config = OllamaMCPConfig(
            model_name="mixtral:latest",
            base_url=REMOTE_OLLAMA_URL,
            temperature=0.7,
            timeout=180.0,
            mcp_servers=mcp_servers,
            max_tool_calls=2
        )
        
        test_model = OllamaWithMCPModel(config=mcp_config)
        print(f"✅ Test model: {test_model.model_name} with MCP")
        print(f"   Available tools: {list(test_model.available_tools.keys())}")
        
        # 3. Initialize evaluators (simpler for demo)
        print("\n⚖️ Initializing Evaluator...")
        from models.ollama_model import OllamaModel, OllamaConfig
        
        evaluator_models = [
            OllamaModel(config=OllamaConfig(
                model_name="llama3.2:latest",
                base_url=REMOTE_OLLAMA_URL,
                timeout=120.0,
                temperature=0.2
            ))
        ]
        evaluator = EvaluatorFactory.create_evaluator(evaluator_models)
        
        # 4. Initialize one MCP metric for demo
        print("\n📊 Initializing MCP Metric...")
        metrics = MetricFactory.create_metrics_by_names(['tool_usage_accuracy'])
        print(f"✅ Using metric: {metrics[0].name}")
        
        # 5. Run demo benchmark
        print("\n🏃 Running MCP Demo...")
        runner = BenchmarkRunner(evaluator, metrics)
        
        print("Generating response with tool usage...")
        benchmark_result = await runner.run_benchmark(test_model, demo_dataset)
        
        print("✅ Demo completed!")
        
        # 6. Show results
        print("\n📈 Demo Results")
        print("=" * 20)
        
        stats = benchmark_result.get_summary_statistics()
        print(f"Overall score: {stats['overall_average']:.2f}/10")
        
        for metric_name, avg_score in stats['average_scores'].items():
            print(f"• {metric_name}: {avg_score:.2f}/10")
        
        # 7. Save demo results
        print(f"\n💾 Saving Demo Results...")
        results_dir = Path("mcp_demo_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_path = results_dir / f"mcp_demo_results_{timestamp}.json"
        benchmark_result.save_to_json_file(str(json_path))
        print(f"✅ Results saved: {json_path}")
        
        # Generate dashboard
        dashboard_path = results_dir / f"mcp_demo_dashboard_{timestamp}.html"
        generate_html_dashboard(benchmark_result, str(dashboard_path))
        print(f"✅ Dashboard saved: {dashboard_path}")
        
        print(f"\n🎉 MCP demo completed successfully!")
        print(f"🌐 Open {dashboard_path.absolute()} to view results")
        print(f"\n🔧 MCP Features Tested:")
        print(f"   • Tool usage detection and evaluation")
        print(f"   • Remote MCP server integration")
        print(f"   • Custom MCP metrics")
        
        return benchmark_result
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"❌ Demo failed: {e}")
        return None


async def main():
    """Main function."""
    result = await demo_mcp_benchmark()
    if result:
        print("\n✅ MCP demo completed successfully!")
        return 0
    else:
        print("\n❌ MCP demo failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 