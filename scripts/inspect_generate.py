#!/usr/bin/env python3
"""
Inspect Ollama generate output using the project's OllamaWithMCPModel wrapper.

Usage: python3 scripts/inspect_generate.py

It will call mixtral:latest with a prompt that requests a JSON tool_call and print the
full ModelResponse (text and metadata) so we can see whether a tool_call was emitted.
"""
import asyncio
import json
import logging
from models.ollama_mcp_model import OllamaWithMCPModel, OllamaMCPConfig, MCPServerConfig

logging.basicConfig(level=logging.DEBUG)

PROMPT = "What's the current weather in Konstanz?"

async def main():
    # Create MCP server config for weather tool
    weather_server = MCPServerConfig(
        name="fogcast-weather",
        url="http://ollama.ios.htwg-konstanz.de:8000",
        description="Weather service for Konstanz, Germany with current conditions, forecasts, and historical data",
        available_tools=[
            "get_current_weather_summary",
            "get_forecast_summary",
            "get_weather_history"
        ]
    )

    cfg = OllamaMCPConfig(
        model_name="mixtral:latest",
        base_url="http://ollama.ios.htwg-konstanz.de:11434",
        timeout=120.0,
        temperature=0.0,
        num_ctx=8192,
        mcp_servers=[weather_server],
        max_tool_calls=3,
        tool_call_timeout=30.0
    )
    model = OllamaWithMCPModel(config=cfg)
    print(f"Calling Ollama MCP model {model.model_name} at {model.base_url}...")
    print(f"Available tools: {list(model.available_tools.keys())}\n")
    try:
        resp = await model.generate(PROMPT, stream=False, max_tokens=512)
        out = {
            "text": resp.text,
            "metadata": resp.metadata,
            "is_successful": getattr(resp, 'is_successful', None)
        }
        print("\n" + "="*80)
        print("RESPONSE:")
        print("="*80)
        print(json.dumps(out, indent=2, default=str))
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())

