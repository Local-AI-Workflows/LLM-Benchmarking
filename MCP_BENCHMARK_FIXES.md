# MCP Benchmark Fixes - Summary

## Issues Fixed

### 1. Tool Calls Not Being Executed
**Problem:** The MCP benchmark was saving the raw JSON tool call in responses instead of executing the tools and getting actual results.

**Root Causes:**
- Tool calls were being extracted from model responses but not properly executed
- Tool results were not being stored in metadata
- The prompt for the second iteration wasn't clear about needing to provide a natural language answer

**Fixes Applied:**

#### a) Enhanced Tool Execution Flow (`models/ollama_mcp_model.py`)
- Added `all_tool_results` list to track all tool execution results
- Improved logging to show when tools are successfully called and what data they return
- Added proper storage of `tool_results` in response metadata
- Fixed the loop logic to continue until no more tool calls are needed

#### b) Improved Prompt Engineering
- **Initial prompt** now clearly instructs the model to respond ONLY with JSON tool calls
- **Follow-up prompt** (after tool execution) explicitly tells the model to:
  - Provide a natural, conversational answer
  - Use the data from tool results  
  - NOT make another tool call
  - Format response as natural text, not JSON

#### c) Better JSON Extraction
- Reordered parsing attempts to try full-response JSON parsing first
- Added better error handling and logging
- More permissive regex patterns for edge cases

#### d) Fixed MCP API Endpoint Structure
- Changed from `/tools/{tool_name}` to `/{tool_name}` to match the actual OpenAPI spec
- Added better error handling for HTTP requests
- Improved timeout handling

### 2. Incorrect Model Selection (Reasoning vs Non-Reasoning)
**Problem:** The benchmark was comparing `mixtral:latest` (non-reasoning) with `deepseek-r1:8b` (reasoning model), which isn't a fair comparison.

**Fix:** 
- Replaced `deepseek-r1:8b` with `qwen2.5:7b`
- Both models are now non-reasoning models for fair comparison
- Updated documentation in the script header

### 3. Incorrect Tool Names
**Problem:** The available tools list had `get_forecast_summary` but the actual API endpoint is `get_future_weather_forecast`.

**Fix:**
- Updated `run_weather_mcp_benchmark.py` to use the correct tool name: `get_future_weather_forecast`
- This aligns with the actual OpenAPI specification shown by the user

## Results

### Before Fixes:
```json
{
  "response": "{\"tool_call\": {\"name\": \"get_current_weather_summary\", \"parameters\": {}}}",
  "metadata": {
    "tool_calls_made": 0,
    "had_tool_calls": false
  }
}
```

### After Fixes:
```json
{
  "response": "Sure thing! The current weather in Konstanz, Germany is quite comfortable. As of my last update on October 26, 2025 at 14:50, the temperature is a mild 9.5 degrees Celsius. The humidity is relatively...",
  "metadata": {
    "tool_calls_made": 1,
    "tool_calls": [{"name": "get_current_weather_summary", "parameters": {}}],
    "tool_results": [{"tool": "get_current_weather_summary", "result": {...}, "success": true}]
  }
}
```

## Files Modified

1. **`models/ollama_mcp_model.py`**
   - Enhanced `generate()` method to properly execute tools and store results
   - Improved `_enhance_prompt_with_tools()` with better instructions
   - Rewrote `_extract_tool_calls()` for more reliable JSON extraction
   - Fixed `_call_mcp_tool()` to use correct API endpoints
   - Updated `_update_prompt_with_tool_results()` to give clear instructions for final answer

2. **`run_weather_mcp_benchmark.py`**
   - Changed models from `deepseek-r1:8b` to `qwen2.5:7b`
   - Fixed tool name from `get_forecast_summary` to `get_future_weather_forecast`
   - Updated documentation to clarify both models are non-reasoning

## Testing

Created `test_mcp_fix.py` to verify the fixes work correctly:
- ✅ Tool calls are extracted from model responses
- ✅ Tools are executed against the MCP server
- ✅ Tool results are received and stored
- ✅ Model provides natural language answer based on tool results
- ✅ Metadata correctly reflects tool usage

## Running the Benchmark

```bash
python3 run_weather_mcp_benchmark.py
```

The benchmark will now:
1. Test both non-reasoning models (mixtral:latest and qwen2.5:7b)
2. Execute actual tool calls to the weather API
3. Store tool calls and results in metadata
4. Generate responses with real weather data
5. Save results to `results/weather_mcp_benchmark/`

## Next Steps

The benchmark is currently running. Once complete, you can:
1. Check the HTML dashboards in `results/weather_mcp_benchmark/`
2. Compare the two non-reasoning models' performance
3. Verify that tool usage metrics now accurately reflect actual tool execution

