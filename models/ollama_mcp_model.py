"""
Ollama model with MCP (Model Context Protocol) support for tool usage.

This model extends the base OllamaModel to support function calling
and tool usage through MCP servers.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
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
    
    async def generate_response_async(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response with potential tool usage."""
        try:
            # Start with the original prompt
            current_prompt = prompt
            tool_calls_made = []
            
            for attempt in range(self.mcp_config.max_tool_calls + 1):
                # Add tool information to prompt if tools are available
                if self.available_tools and attempt == 0:
                    current_prompt = self._enhance_prompt_with_tools(prompt)
                
                # Generate response from Ollama
                response = await super().generate_response_async(current_prompt, **kwargs)
                
                # Check if the response contains tool calls
                tool_calls = self._extract_tool_calls(response.content)
                
                if not tool_calls or attempt >= self.mcp_config.max_tool_calls:
                    # No tool calls or max attempts reached
                    break
                
                # Execute tool calls
                tool_results = await self._execute_tool_calls(tool_calls)
                tool_calls_made.extend(tool_calls)
                
                # Update prompt with tool results for next iteration
                current_prompt = self._update_prompt_with_tool_results(
                    current_prompt, tool_calls, tool_results
                )
            
            # Add tool usage metadata to response
            if tool_calls_made:
                response.metadata = response.metadata or {}
                response.metadata['tool_calls'] = tool_calls_made
                response.metadata['tool_usage_count'] = len(tool_calls_made)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in MCP model generation: {e}")
            # Fallback to regular generation without tools
            return await super().generate_response_async(prompt, **kwargs)
    
    def _enhance_prompt_with_tools(self, prompt: str) -> str:
        """Add tool information to the prompt."""
        tool_descriptions = []
        for tool_name, tool_info in self.available_tools.items():
            tool_descriptions.append(f"- {tool_name}: {tool_info['description']}")
        
        tools_text = "\n".join(tool_descriptions)
        
        enhanced_prompt = f"""You have access to the following tools:
{tools_text}

To use a tool, include a JSON object in your response with this format:
{{"tool_call": {{"name": "tool_name", "parameters": {{"param": "value"}}}}}}

Original request: {prompt}

Please provide a helpful response, using tools when appropriate to get accurate, up-to-date information."""
        
        return enhanced_prompt
    
    def _extract_tool_calls(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract tool calls from the response text."""
        tool_calls = []
        
        try:
            # Look for JSON objects with tool_call structure
            import re
            
            # Pattern to match tool call JSON objects
            pattern = r'\{"tool_call":\s*\{[^}]+\}\}'
            matches = re.findall(pattern, response_text)
            
            for match in matches:
                try:
                    tool_call_data = json.loads(match)
                    if 'tool_call' in tool_call_data:
                        tool_calls.append(tool_call_data['tool_call'])
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error extracting tool calls: {e}")
        
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
        
        # Construct API call to MCP server
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.mcp_config.tool_call_timeout)) as session:
            # This depends on your MCP server API structure
            # Assuming a REST-like interface for the proxy
            endpoint = f"{server_url}/tools/{tool_name}"
            
            async with session.post(endpoint, json=parameters) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Tool call failed: {response.status} - {error_text}")
    
    def _update_prompt_with_tool_results(self, prompt: str, tool_calls: List[Dict], results: List[Dict]) -> str:
        """Update prompt with tool call results for next iteration."""
        tool_results_text = "\n\nTool call results:\n"
        
        for tool_call, result in zip(tool_calls, results):
            tool_name = tool_call.get('name', 'unknown')
            if 'error' in result:
                tool_results_text += f"- {tool_name}: Error - {result['error']}\n"
            else:
                tool_results_text += f"- {tool_name}: {json.dumps(result.get('result', 'No result'), indent=2)}\n"
        
        return prompt + tool_results_text + "\n\nPlease provide a final response based on this information:"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information including MCP capabilities."""
        info = super().get_model_info()
        info.update({
            'mcp_enabled': True,
            'available_tools': list(self.available_tools.keys()),
            'mcp_servers': [server.name for server in self.mcp_config.mcp_servers]
        })
        return info 