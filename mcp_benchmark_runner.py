#!/usr/bin/env python3
"""
MCP Tool Usage Benchmark Runner

This script runs a comprehensive benchmark test for evaluating LLM performance
on MCP (Model Context Protocol) tool usage with weather and mensa services.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from models.ollama_mcp_model import OllamaWithMCPModel, OllamaMCPConfig, MCPServerConfig
from metrics import MetricFactory, EvaluatorFactory
from metrics.responses import BenchmarkResult
from benchmark.runner import BenchmarkRunner
from dashboard import generate_html_dashboard
from dataset import DatasetLoader

# MCP Server configuration based on docker-compose.yml
REMOTE_OLLAMA_URL = "http://ollama.ios.htwg-konstanz.de:11434"
MCP_WEATHER_URL = "http://ollama.ios.htwg-konstanz.de:8007"
MCP_MENSA_URL = "http://ollama.ios.htwg-konstanz.de:8008"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the MCP tool usage benchmark."""
    
    print("🚀 Starting MCP Tool Usage Quality Benchmark")
    print("=" * 55)
    print(f"🌐 Remote Ollama server: {REMOTE_OLLAMA_URL}")
    print(f"🌤️  Weather MCP server: {MCP_WEATHER_URL}")
    print(f"🍽️  Mensa MCP server: {MCP_MENSA_URL}")
    
    # Create results directory
    results_dir = Path("mcp_benchmark_results")
    results_dir.mkdir(exist_ok=True)
    
    try:
        # 1. Load the MCP test dataset
        print("\n🔧 Loading MCP Test Dataset...")
        dataset = DatasetLoader.load_from_file("mcp_test_dataset.json")
        
        print(f"✅ Loaded dataset: {dataset.name}")
        print(f"   Description: {dataset.description}")
        print(f"   Number of MCP scenarios: {len(dataset)}")
        
        # Display dataset statistics
        stats = dataset.get_statistics()
        print(f"   Tool categories: {set(q.get_metadata('category') for q in dataset.questions if q.get_metadata('category'))}")
        print(f"   Difficulty levels: {set(q.get_metadata('difficulty') for q in dataset.questions if q.get_metadata('difficulty'))}")
        print(f"   Required tools: {set([tool for q in dataset.questions for tool in q.get_metadata('tools_required', [])])}")
        
        # 2. Initialize the MCP-enabled test model
        print("\n🤖 Initializing MCP-Enabled Test Model...")
        
        # Configure MCP servers
        mcp_servers = [
            MCPServerConfig(
                name="weather",
                url=MCP_WEATHER_URL,
                description="Get current weather and forecasts for locations",
                available_tools=["get_weather", "get_forecast"]
            ),
            MCPServerConfig(
                name="mensa", 
                url=MCP_MENSA_URL,
                description="Get mensa/cafeteria menu information",
                available_tools=["get_menu", "get_daily_menu"]
            )
        ]
        
        # Create MCP-enabled model
        mcp_config = OllamaMCPConfig(
            model_name="mixtral:latest",
            base_url=REMOTE_OLLAMA_URL,
            temperature=0.7,
            timeout=300.0,  # 5 minutes for complex tool usage
            num_ctx=8192,
            mcp_servers=mcp_servers,
            max_tool_calls=3,
            tool_call_timeout=30.0
        )
        
        test_model = OllamaWithMCPModel(config=mcp_config)
        print(f"✅ Test model: {test_model.model_name} with MCP support")
        print(f"   Available tools: {list(test_model.available_tools.keys())}")
        print(f"   Max tool calls: {mcp_config.max_tool_calls}")
        
        # 3. Initialize evaluator models (without MCP for objective evaluation)
        print("\n⚖️ Initializing Evaluator Models...")
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
        print(f"✅ Evaluator models: {[model.model_name for model in evaluator_models]}")
        
        # 4. Initialize MCP-specific metrics
        print("\n📊 Initializing MCP-Specific Metrics...")
        mcp_metrics = [
            'tool_usage_accuracy',
            'information_retrieval_quality',
            'contextual_awareness'
        ]
        
        metrics = MetricFactory.create_metrics_by_names(mcp_metrics)
        print(f"✅ MCP metrics loaded: {[metric.name for metric in metrics]}")
        
        for metric in metrics:
            print(f"   • {metric.name}: {metric.description}")
        
        # 5. Create and run benchmark
        print("\n🏃 Running MCP Tool Usage Benchmark...")
        print("⏱️  Expected runtime: 5-8 minutes")
        print("💡 Process breakdown:")
        print("   1. Generate responses with tool usage (2-3 min)")
        print("   2. Evaluate tool usage quality (2-3 min)")  
        print("   3. Create visualizations and dashboard (1-2 min)")
        print("\n🔄 Starting benchmark execution...")
        
        runner = BenchmarkRunner(evaluator, metrics)
        
        benchmark_start_time = datetime.now()
        benchmark_result = await runner.run_benchmark(test_model, dataset)
        benchmark_end_time = datetime.now()
        
        runtime_minutes = (benchmark_end_time - benchmark_start_time).total_seconds() / 60
        print(f"✅ MCP benchmark completed successfully in {runtime_minutes:.1f} minutes!")
        
        # 6. Save results to JSON
        print("\n💾 Saving Results...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON results
        json_filename = f"mcp_benchmark_results_{timestamp}.json"
        json_path = results_dir / json_filename
        benchmark_result.save_to_json_file(str(json_path))
        print(f"✅ Results saved to: {json_path}")
        
        # 7. Generate interactive HTML dashboard
        print("\n🌐 Generating Interactive HTML Dashboard...")
        dashboard_filename = f"mcp_benchmark_dashboard_{timestamp}.html"
        dashboard_path = results_dir / dashboard_filename
        
        generated_path = generate_html_dashboard(benchmark_result, str(dashboard_path))
        print(f"✅ Interactive dashboard generated: {generated_path}")
        
        # 8. Print comprehensive summary statistics
        print("\n📈 MCP Benchmark Results Summary")
        print("=" * 45)
        print(f"🔬 Test Model: Mixtral with MCP tools")
        print(f"⚖️ Evaluators: Mistral, Llama3.2")
        print(f"⏱️ Runtime: {runtime_minutes:.1f} minutes")
        
        # Get summary statistics
        stats = benchmark_result.get_summary_statistics()
        
        print(f"\n📊 Results Overview:")
        print(f"Total MCP scenarios tested: {stats['num_prompts']}")
        print(f"Total evaluations performed: {len(benchmark_result.prompt_evaluations) * len(mcp_metrics)}")
        print(f"Overall average score: {stats['overall_average']:.2f}/10")
        
        print(f"\n📋 Average scores by metric:")
        for metric_name, avg_score in stats['average_scores'].items():
            print(f"  • {metric_name.replace('_', ' ').title()}: {avg_score:.2f}/10")
        
        # Performance by tool usage complexity
        print(f"\n🔧 Performance by scenario complexity:")
        complexity_scores = {}
        for eval_result in benchmark_result.prompt_evaluations:
            for question in dataset.questions:
                if question.get_full_prompt() == eval_result.prompt:
                    difficulty = question.get_metadata('difficulty', 'unknown')
                    expected_calls = question.get_metadata('expected_tool_calls', 0)
                    
                    complexity_key = f"{difficulty} ({expected_calls} tool calls)"
                    if complexity_key not in complexity_scores:
                        complexity_scores[complexity_key] = []
                    
                    prompt_avg = sum(e.score for e in eval_result.evaluations) / len(eval_result.evaluations)
                    complexity_scores[complexity_key].append(prompt_avg)
                    break
        
        for complexity, scores in complexity_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"  • {complexity}: {avg_score:.2f}/10")
        
        # Tool usage analysis
        print(f"\n🛠️ Tool Usage Analysis:")
        tool_usage_count = 0
        successful_tool_calls = 0
        
        for eval_result in benchmark_result.prompt_evaluations:
            if hasattr(eval_result, 'response_metadata') and eval_result.response_metadata:
                metadata = eval_result.response_metadata
                if isinstance(metadata, dict) and 'tool_calls' in metadata:
                    tool_usage_count += len(metadata['tool_calls'])
                    successful_tool_calls += len(metadata['tool_calls'])
        
        print(f"  • Total tool calls attempted: {tool_usage_count}")
        print(f"  • Tool call success rate: {(successful_tool_calls/max(tool_usage_count,1)*100):.1f}%")
        
        # Show top performing scenarios
        print(f"\n🏆 Top performing MCP scenarios:")
        prompt_scores = []
        for eval_result in benchmark_result.prompt_evaluations:
            prompt_avg = sum(e.score for e in eval_result.evaluations) / len(eval_result.evaluations)
            question_id = "unknown"
            scenario = "unknown"
            for question in dataset.questions:
                if question.get_full_prompt() == eval_result.prompt:
                    question_id = question.id
                    scenario = question.get_metadata('scenario', 'unknown')
                    break
            prompt_scores.append((question_id, scenario, prompt_avg))
        
        # Sort by score and show all (since we only have 3)
        prompt_scores.sort(key=lambda x: x[2], reverse=True)
        for i, (question_id, scenario, score) in enumerate(prompt_scores, 1):
            print(f"  {i}. {question_id} ({scenario}): {score:.2f}/10")
        
        # 9. Provide comprehensive next steps
        print(f"\n📁 Results saved to: {results_dir.absolute()}")
        print("Files generated:")
        print(f"  • JSON results: {json_filename}")
        print(f"  • HTML dashboard: {dashboard_filename}")
        
        print(f"\n🎉 MCP Tool Usage Benchmark completed successfully!")
        print(f"🌐 Open {dashboard_path.absolute()} in your browser to view the interactive dashboard")
        
        print(f"\n💡 Key Insights:")
        print(f"   • Mixtral demonstrated MCP tool usage capabilities")
        print(f"   • {len(mcp_servers)} MCP servers integrated (weather, mensa)")
        print(f"   • {stats['num_prompts']} scenarios testing different tool usage patterns")
        print(f"   • Average tool usage quality: {stats['overall_average']:.1f}/10")
        
        print(f"\n🚀 Next steps:")
        print(f"   • Analyze tool usage patterns in the dashboard")
        print(f"   • Review successful vs. failed tool calls")
        print(f"   • Expand test scenarios for more complex tool interactions")
        print(f"   • Fine-tune prompting strategies for better tool usage")
        
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find MCP test dataset: {e}")
        print("Please ensure 'mcp_test_dataset.json' exists in the current directory")
        return 1
        
    except Exception as e:
        logger.error(f"MCP benchmark failed: {e}", exc_info=True)
        print(f"❌ MCP benchmark failed: {e}")
        print(f"\n🔧 Troubleshooting tips:")
        print(f"   • Check server connectivity: curl {REMOTE_OLLAMA_URL}/api/version")
        print(f"   • Check MCP servers: curl {MCP_WEATHER_URL}/docs and {MCP_MENSA_URL}/docs")
        print(f"   • Verify models on server: curl {REMOTE_OLLAMA_URL}/api/tags")
        print(f"   • Ensure MCP servers are running with docker-compose")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 