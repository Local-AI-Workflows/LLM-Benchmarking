"""
Ollama model with MCP (Model Context Protocol) support for tool usage.

This model extends the base OllamaModel to support function calling
and tool usage through MCP servers.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
import aiohttp
from dataclasses import dataclass
from pydantic import Field

from .ollama_model import OllamaModel, OllamaConfig
from .responses import ModelResponse

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    url: str
    description: str
    available_tools: List[str] = None


class OllamaMCPConfig(OllamaConfig):
    """Configuration for Ollama model with MCP support."""
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list, description="List of MCP servers")
    max_tool_calls: int = Field(default=3, ge=1, le=10, description="Maximum number of tool calls per request")
    tool_call_timeout: float = Field(default=30.0, gt=0, description="Timeout for tool calls in seconds")


class OllamaWithMCPModel(OllamaModel):
    """Ollama model with MCP tool usage capabilities."""
    
    def __init__(self, config: OllamaMCPConfig):
        """Initialize Ollama model with MCP support."""
        super().__init__(config)
        self.mcp_config = config
        self.available_tools = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize available tools from MCP servers."""
        for server in self.mcp_config.mcp_servers:
            for tool in (server.available_tools or []):
                self.available_tools[tool] = {
                    'server': server.name,
                    'url': server.url,
                    'description': server.description
                }
        
        logger.info(f"Initialized MCP model with {len(self.available_tools)} tools: {list(self.available_tools.keys())}")
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response with potential tool usage."""
        response = None
        try:
            current_prompt = prompt
            tool_calls_made = []
            original_response = None
            all_tool_results = []

            logger.info(f"Starting MCP generation with prompt: {prompt[:100]}...")
            logger.info(f"Available tools: {list(self.available_tools.keys())}")

            for attempt in range(self.mcp_config.max_tool_calls + 1):
                if self.available_tools and attempt == 0:
                    current_prompt = self._enhance_prompt_with_tools(prompt)
                    logger.info(f"Enhanced prompt with tools (length: {len(current_prompt)})")

                logger.info(f"MCP attempt {attempt + 1}/{self.mcp_config.max_tool_calls + 1}")
                response = await super().generate(current_prompt, **kwargs)

                logger.info(f"Got response (length: {len(response.text)}): {response.text[:200]}...")

                if attempt == 0:
                    original_response = response.text

                tool_calls = self._extract_tool_calls(response.text)
                logger.info(f"Extracted {len(tool_calls)} tool calls from response")

                if not tool_calls:
                    if attempt == 0:
                        logger.warning("No tool calls found on first attempt - model may not be following instructions")
                    # If we already made tool calls in previous iterations, break to return final answer
                    if tool_calls_made:
                        logger.info("No more tool calls needed, using current response as final answer")
                    break
                
                if attempt >= self.mcp_config.max_tool_calls:
                    logger.info(f"Reached max tool calls limit ({self.mcp_config.max_tool_calls})")
                    break

                # Execute the tool calls
                logger.info(f"Executing {len(tool_calls)} tool calls: {[tc.get('name') for tc in tool_calls]}")
                tool_results = await self._execute_tool_calls(tool_calls)
                tool_calls_made.extend(tool_calls)
                all_tool_results.extend(tool_results)

                logger.info(f"Tool results received: {len(tool_results)} results")
                for i, result in enumerate(tool_results):
                    if 'error' in result:
                        logger.error(f"Tool {result.get('tool')} error: {result['error']}")
                    else:
                        logger.info(f"Tool {result.get('tool')} success: {str(result.get('result', ''))[:100]}...")

                # Update prompt with tool results for next iteration
                current_prompt = self._update_prompt_with_tool_results(
                    prompt, tool_calls, tool_results
                )
            
            # Store metadata about tool usage
            if response:
                response.metadata = response.metadata or {}
                if tool_calls_made:
                    response.metadata['tool_calls'] = tool_calls_made
                    response.metadata['tool_results'] = all_tool_results
                    response.metadata['tool_usage_count'] = len(tool_calls_made)
                    response.metadata['original_response'] = original_response
                    logger.info(f"Final response includes {len(tool_calls_made)} tool calls with results")
                else:
                    response.metadata['tool_usage_count'] = 0
                    logger.warning("No tool calls were made during generation")

            return response
            
        except Exception as e:
            logger.error(f"Error in MCP model generation: {e}", exc_info=True)
            return await super().generate(prompt, **kwargs)

    def _enhance_prompt_with_tools(self, prompt: str) -> str:
        """Add tool information to the prompt."""
        tool_descriptions = []
        for tool_name, tool_info in self.available_tools.items():
            tool_descriptions.append(f"- {tool_name}: {tool_info['description']}")
        
        tools_text = "\n".join(tool_descriptions)
        
        enhanced_prompt = f"""You are an AI assistant with access to real-time weather tools. You MUST use these tools when asked for weather information.

AVAILABLE TOOLS:
{tools_text}

TOOL USAGE PROTOCOL:
1. When the user asks about CURRENT weather, use: get_current_weather_summary
2. When the user asks about FUTURE weather (tomorrow, next week, etc.), use: get_future_weather_forecast
3. When the user asks about PAST weather (yesterday, last week, etc.), use: get_weather_history

To call a tool, respond with ONLY a JSON object in this EXACT format:
{{"tool_call": {{"name": "tool_name", "parameters": {{}}}}}}

Examples:
- For "What's the weather in Konstanz?": {{"tool_call": {{"name": "get_current_weather_summary", "parameters": {{}}}}}}
- For "What will the weather be tomorrow?": {{"tool_call": {{"name": "get_future_weather_forecast", "parameters": {{"days_offset": 1}}}}}}
- For "What was the weather yesterday?": {{"tool_call": {{"name": "get_weather_history", "parameters": {{"days_offset": -1}}}}}}

USER REQUEST: {prompt}

IMPORTANT: Respond ONLY with the tool call JSON. Do NOT add explanatory text or disclaimers."""

        return enhanced_prompt
    
    def _extract_tool_calls(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract tool calls from the response text."""
        tool_calls = []
        
        try:
            import re
            
            # Log the response for debugging
            logger.info(f"Extracting tool calls from response (length {len(response_text)}): {response_text[:500]}...")
            logger.debug(f"Full response: {response_text}")

            # First, try parsing the entire response as JSON
            try:
                parsed = json.loads(response_text.strip())
                if isinstance(parsed, dict) and 'tool_call' in parsed:
                    tool_call = parsed['tool_call']
                    logger.info(f"Successfully parsed entire response as tool call JSON: {tool_call}")
                    tool_calls.append(tool_call)
                    return tool_calls
            except json.JSONDecodeError as e:
                logger.debug(f"Could not parse entire response as JSON: {e}")

            # Try multiple regex patterns to extract tool calls
            patterns = [
                # More permissive pattern that captures nested braces better
                r'\{\s*["\']?tool_call["\']?\s*:\s*\{(?:[^{}]|\{[^{}]*\})*\}\s*\}',
                # Standard single-line format
                r'\{"tool_call":\s*\{[^}]+\}\}',
                # Multi-line format with nested braces
                r'\{"tool_call":\s*\{[^}]*(?:\{[^}]*\})?[^}]*\}\}',
            ]

            matches = []
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, response_text, re.DOTALL)
                if matches:
                    logger.info(f"Found {len(matches)} potential tool calls with pattern {i+1}")
                    break

            # Process matches
            for match in matches:
                try:
                    # Clean up the match (remove extra whitespace, etc.)
                    cleaned_match = match.strip()
                    logger.debug(f"Trying to parse match: {cleaned_match}")

                    tool_call_data = json.loads(cleaned_match)
                    if 'tool_call' in tool_call_data:
                        tool_call = tool_call_data['tool_call']
                        logger.info(f"Extracted tool call: {tool_call}")
                        tool_calls.append(tool_call)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse tool call JSON: {e} - Match was: {match[:100]}")
                    continue

            if not tool_calls:
                logger.warning("No valid tool calls found in response")

        except Exception as e:
            logger.warning(f"Error extracting tool calls: {e}", exc_info=True)

        return tool_calls
    
    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tool calls against MCP servers."""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get('name')
            parameters = tool_call.get('parameters', {})
            
            if tool_name not in self.available_tools:
                results.append({
                    'tool': tool_name,
                    'error': f'Tool {tool_name} not available'
                })
                continue
            
            try:
                result = await self._call_mcp_tool(tool_name, parameters)
                results.append({
                    'tool': tool_name,
                    'parameters': parameters,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                results.append({
                    'tool': tool_name,
                    'parameters': parameters,
                    'error': str(e)
                })
        
        return results
    
    async def _call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Call a specific tool on its MCP server."""
        tool_info = self.available_tools[tool_name]
        server_url = tool_info['url']
        
        logger.info(f"Calling MCP tool {tool_name} at {server_url} with parameters: {parameters}")

        # The OpenAPI spec shows endpoints like /get_current_weather_summary (POST)
        # with request body containing the parameters
        endpoint = f"{server_url}/{tool_name}"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.mcp_config.tool_call_timeout)) as session:
            try:
                async with session.post(endpoint, json=parameters) as response:
                    response_text = await response.text()
                    logger.info(f"Tool {tool_name} response status: {response.status}")
                    logger.debug(f"Tool {tool_name} response body: {response_text[:500]}")

                    if response.status == 200:
                        # Try to parse as JSON, but return text if that fails
                        try:
                            return json.loads(response_text)
                        except json.JSONDecodeError:
                            return response_text
                    else:
                        raise Exception(f"Tool call failed with status {response.status}: {response_text}")
            except asyncio.TimeoutError:
                raise Exception(f"Tool call timed out after {self.mcp_config.tool_call_timeout} seconds")
            except aiohttp.ClientError as e:
                raise Exception(f"HTTP client error: {str(e)}")

    def _update_prompt_with_tool_results(self, prompt: str, tool_calls: List[Dict], results: List[Dict]) -> str:
        """Update prompt with tool call results for next iteration."""
        tool_results_text = "\n\nTOOL EXECUTION RESULTS:\n"

        for tool_call, result in zip(tool_calls, results):
            tool_name = tool_call.get('name', 'unknown')
            if 'error' in result:
                tool_results_text += f"\n[{tool_name}] ERROR: {result['error']}\n"
            else:
                result_data = result.get('result', 'No result')
                tool_results_text += f"\n[{tool_name}] SUCCESS:\n{json.dumps(result_data, indent=2)}\n"

        updated_prompt = f"""ORIGINAL USER REQUEST: {prompt}

{tool_results_text}

INSTRUCTIONS: Based on the tool results above, provide a natural, helpful answer to the user's question. 
- Use the data from the tool results
- Be conversational and friendly
- Include specific numbers and details from the results
- Do NOT make another tool call - just answer the question
- Format your response as natural text, not JSON

Your answer:"""

        return updated_prompt

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information including MCP capabilities."""
        info = super().get_model_info()
        info.update({
            'mcp_enabled': True,
            'available_tools': list(self.available_tools.keys()),
            'mcp_servers': [server.name for server in self.mcp_config.mcp_servers]
        })
        return info 