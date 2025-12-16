#!/usr/bin/env python3
"""Quick test to verify MCP tool calling works correctly."""
import asyncio
import logging
from models.ollama_mcp_model import OllamaWithMCPModel, OllamaMCPConfig, MCPServerConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def main():
    print("="*80)
    print("Testing MCP Tool Execution Fix")
    print("="*80)
    
    # Configure MCP model
    config = OllamaMCPConfig(
        model_name="mixtral:latest",
        base_url="http://ollama.ios.htwg-konstanz.de:11434",
        temperature=0.7,
        timeout=120.0,
        num_ctx=4096,
        mcp_servers=[
            MCPServerConfig(
                name="fogcast-weather",
                url="http://ollama.ios.htwg-konstanz.de:8000",
                description="Weather service for Konstanz",
                available_tools=["get_current_weather_summary", "get_future_weather_forecast", "get_weather_history"]
            )
        ],
        max_tool_calls=3,
        tool_call_timeout=30.0
    )
    
    model = OllamaWithMCPModel(config=config)
    print(f"\nModel: {model.model_name}")
    print(f"Available tools: {list(model.available_tools.keys())}")
    
    # Test prompt
    prompt = "What's the current weather in Konstanz?"
    print(f"\nPrompt: {prompt}")
    print("\nGenerating response...\n")
    
    try:
        response = await model.generate(prompt)
        
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"\nResponse text ({len(response.text)} chars):")
        print("-" * 40)
        print(response.text)
        print("-" * 40)
        
        if response.metadata:
            print(f"\nTool calls made: {response.metadata.get('tool_usage_count', 0)}")
            if 'tool_calls' in response.metadata:
                print(f"Tool calls: {response.metadata['tool_calls']}")
            if 'tool_results' in response.metadata:
                print(f"\nTool results:")
                for result in response.metadata['tool_results']:
                    print(f"  - {result.get('tool')}: ", end="")
                    if 'error' in result:
                        print(f"ERROR - {result['error']}")
                    else:
                        print(f"SUCCESS")
        
        print("\n" + "="*80)
        print("Test completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

