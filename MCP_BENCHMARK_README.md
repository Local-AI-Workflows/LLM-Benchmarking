# MCP Tool Usage Benchmark

A comprehensive benchmark for evaluating LLM performance with **Model Context Protocol (MCP)** tool usage, based on the [Local-AI project](https://github.com/Sprayer115/Local-AI).

## 🎯 **Overview**

This benchmark evaluates how well Large Language Models use external tools through the Model Context Protocol. It tests real-world scenarios involving weather information and university mensa (cafeteria) data retrieval.

## 📁 **Project Structure**

```
metrics/
├── mcp/                              # MCP-specific evaluation metrics
│   ├── tool_usage_accuracy.py       # Tool selection and execution accuracy
│   ├── information_retrieval_quality.py  # Quality of retrieved information
│   └── contextual_awareness.py      # Context-aware decision making
models/
└── ollama_mcp_model.py              # Ollama model with MCP tool support
mcp_test_dataset.json                # Test scenarios for MCP evaluation
mcp_benchmark_runner.py              # Full MCP benchmark execution
demo_mcp_benchmark.py                # Quick demo with 1 scenario
```

## 🔧 **MCP Server Configuration**

Based on the [Local-AI docker-compose.yml](https://github.com/Sprayer115/Local-AI):

### **Required Services**
- **Weather Service**: `http://ollama.ios.htwg-konstanz.de:8007`
- **Mensa Service**: `http://ollama.ios.htwg-konstanz.de:8008`
- **Ollama Server**: `http://ollama.ios.htwg-konstanz.de:11434`

### **Available Tools**
- `get_weather` - Current weather for locations
- `get_forecast` - Weather forecasts
- `get_menu` - Mensa menu information
- `get_daily_menu` - Daily mensa offerings

## 📊 **Custom MCP Metrics**

### **1. Tool Usage Accuracy** (`tool_usage_accuracy`)
Evaluates technical correctness of tool usage:
- **Tool Selection** (30%) - Appropriate tool choices
- **Parameter Accuracy** (25%) - Correct parameter formatting
- **Result Integration** (25%) - Proper use of tool outputs
- **Error Handling** (20%) - Graceful error management

### **2. Information Retrieval Quality** (`information_retrieval_quality`)
Assesses quality of information gathering:
- **Retrieval Completeness** (25%) - All necessary data collected
- **Information Relevance** (25%) - Relevant to user query
- **Data Accuracy** (25%) - Current and reliable information
- **Synthesis** (25%) - Well-integrated final response

### **3. Contextual Awareness** (`contextual_awareness`)
Measures intelligent, context-aware tool usage:
- **Context Understanding** (30%) - Full request comprehension
- **Situational Appropriateness** (25%) - Context-appropriate responses
- **Adaptive Behavior** (25%) - Dynamic tool usage decisions
- **User Experience** (20%) - User-friendly communication

## 🧪 **Test Scenarios**

### **Dataset: 3 MCP Scenarios**

1. **Weather Query** (`mcp_001`) - *Easy*
   - Simple weather lookup for outdoor activity planning
   - Tests basic tool usage and recommendation generation

2. **Mensa Menu Planning** (`mcp_002`) - *Medium*  
   - Multi-day menu retrieval with dietary preferences
   - Tests multiple tool calls and filtering capabilities

3. **Event Planning** (`mcp_003`) - *Hard*
   - Complex scenario requiring both weather and mensa tools
   - Tests multi-tool integration and comprehensive planning

## 🚀 **Quick Start**

### **Prerequisites**
```bash
# Ensure MCP servers are running
curl http://ollama.ios.htwg-konstanz.de:8007/docs  # Weather service
curl http://ollama.ios.htwg-konstanz.de:8008/docs  # Mensa service
curl http://ollama.ios.htwg-konstanz.de:11434/api/version  # Ollama
```

### **Run Demo (1 scenario)**
```bash
python3 demo_mcp_benchmark.py
```

### **Run Full Benchmark (3 scenarios)**
```bash
python3 mcp_benchmark_runner.py
```

## 📈 **Expected Results**

### **Performance Indicators**
- **Tool Call Success Rate** - Percentage of successful tool executions
- **Information Quality** - Relevance and accuracy of retrieved data
- **Context Integration** - How well tools serve the user's intent
- **Error Recovery** - Handling of failed tool calls

### **Typical Runtime**
- **Demo**: 2-3 minutes (1 scenario)
- **Full Benchmark**: 5-8 minutes (3 scenarios)

## 🔍 **Understanding Results**

### **Dashboard Analysis**
The generated HTML dashboard includes:
- **Tool Usage Patterns** - Which tools were called when
- **Success/Failure Analysis** - Tool call effectiveness
- **Response Quality** - Integration of tool data into answers
- **Contextual Adaptation** - Situation-appropriate tool usage

### **Score Interpretation**
- **9-10**: Excellent tool usage with perfect integration
- **7-8**: Good tool usage with minor issues
- **5-6**: Adequate tool usage with some problems
- **1-4**: Poor tool usage or integration failures

## 🛠️ **Technical Architecture**

### **OllamaWithMCPModel**
Extends the base `OllamaModel` with:
- **Tool Discovery** - Automatic registration of available MCP tools
- **Tool Call Extraction** - Parsing tool calls from model responses
- **Tool Execution** - HTTP calls to MCP servers
- **Result Integration** - Incorporating tool outputs into responses

### **Tool Call Format**
```json
{"tool_call": {"name": "get_weather", "parameters": {"location": "Konstanz, Germany"}}}
```

### **MCP Server Integration**
- **HTTP Proxy** - mcpo provides HTTP interface to MCP tools
- **Error Handling** - Graceful degradation on tool failures
- **Timeout Management** - Prevents hanging on slow tool calls

## 🔧 **Troubleshooting**

### **Common Issues**

**MCP Servers Not Responding**
```bash
# Check if services are running
docker ps | grep mcp
# Restart if needed
cd /path/to/Local-AI && docker-compose up -d
```

**Tool Calls Not Detected**
- Verify model is using proper JSON format for tool calls
- Check tool call extraction regex patterns
- Review model temperature (too high may break JSON)

**Timeout Errors**
- Increase `tool_call_timeout` in `OllamaMCPConfig`
- Check network connectivity to MCP servers
- Verify server capacity and load

## 📚 **Integration with Main Framework**

### **Metrics Organization**
```python
from metrics import MetricFactory

# Get all MCP metrics
mcp_metrics = MetricFactory.get_metrics_by_category('mcp')

# Create specific MCP metrics
metrics = MetricFactory.create_metrics_by_names([
    'tool_usage_accuracy',
    'information_retrieval_quality', 
    'contextual_awareness'
])
```

### **Model Usage**
```python
from models import OllamaWithMCPModel, OllamaMCPConfig, MCPServerConfig

# Configure MCP servers
servers = [
    MCPServerConfig(name="weather", url="http://...:8007", 
                   description="Weather data", available_tools=["get_weather"])
]

# Create MCP-enabled model
config = OllamaMCPConfig(model_name="mixtral:latest", mcp_servers=servers)
model = OllamaWithMCPModel(config)
```

## 🎯 **Future Enhancements**

### **Additional Tools**
- **File Operations** - Reading/writing documents
- **Web Search** - Information retrieval from web
- **Database Queries** - Structured data access
- **API Integrations** - Third-party service calls

### **Advanced Metrics**
- **Tool Efficiency** - Minimize unnecessary tool calls
- **Multi-step Planning** - Complex task decomposition  
- **Error Recovery** - Intelligent fallback strategies
- **Security Awareness** - Safe tool parameter handling

### **Extended Scenarios**
- **Multi-turn Conversations** - Tool usage across dialogue
- **Complex Workflows** - Multi-tool task orchestration
- **Real-time Data** - Dynamic information updates
- **User Preference Learning** - Adaptive tool selection

## 📄 **Related Documentation**

- [Local-AI Repository](https://github.com/Sprayer115/Local-AI) - MCP server implementations
- [Email Benchmark README](EMAIL_BENCHMARK_README.md) - Email evaluation framework
- [Main Framework README](README.md) - Core benchmarking system

## 🤝 **Contributing**

To add new MCP tools or scenarios:

1. **Add Tool Configuration** in MCP server docker-compose
2. **Create Test Scenarios** in `mcp_test_dataset.json`
3. **Update Tool Lists** in `MCPServerConfig` instances
4. **Test Integration** with `demo_mcp_benchmark.py`

---

**MCP benchmark enables evaluation of real-world tool usage patterns, moving beyond text generation to interactive AI capabilities!** 🚀 