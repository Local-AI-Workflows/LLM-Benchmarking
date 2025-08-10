# LLM Benchmarking Framework
## A Comprehensive Tool for Custom Model Evaluation

---

## Key Features & Overview

### Core Capabilities
- **LLM-as-a-Judge** - Multi-model evaluation for robust scoring
- **Customizable Metrics** - Define domain-specific evaluation criteria
- **Interactive Dashboards** - Rich visualizations and detailed analysis

### Quick Facts
- Built in Python
- Supports local and remote Ollama models
- Extensible metric system via inheritance
- Real-time progress tracking
- Comprehensive result export (JSON + HTML)

---

## Technical Deep Dive

### Creating Custom Metrics
```python
class EmailProfessionalismMetric(StandardMetric):
    def __init__(self):
        super().__init__(
            name="email_professionalism",
            description="Evaluates business communication standards",
            evaluation_instructions="""
            Evaluate on 1-10 scale considering:
            • Tone appropriateness (25%)
            • Structure and clarity (25%) 
            • Business appropriateness (25%)
            • Communication effectiveness (25%)
            """,
            scale_min=1, scale_max=10
        )
```

### Judge Model Prompts
- **Evaluation Instructions** embedded in metric definitions
- **Standardized Scale** (1-10) with clear criteria
- **Context-Aware** prompts with domain knowledge
- **Rationale Required** for transparency and debugging

### Multi-Model Evaluation
- Multiple judge models for consensus scoring
- Automatic aggregation and disagreement analysis
- Individual rationales preserved for analysis
- Correlation analysis between different judges

---

## Architecture Overview

### Processing Pipeline
1. **Dataset Loading** → Parse questions with metadata
2. **Response Generation** → Test model produces answers
3. **Batch Evaluation** → Judge models score responses
4. **Result Aggregation** → Combine scores and statistics
5. **Visualization** → Generate dashboard and charts

### Model Factory System
- **Ollama Models** (local/remote)
- **OpenAI Models** (future extensibility)
- **Configuration Management** (timeouts, parameters)
- **Error Handling** and retry logic

---

## Email Response Quality Benchmark

### Dataset Overview
- **20 Business Scenarios** across diverse contexts
- **Email Types**: Internal (7) + External (13)
- **Difficulty Levels**: Easy (6), Medium (10), Hard (4)
- **Scenarios**: Deadline changes, complaints, celebrations, crises

### Custom Email Metrics
- **Professionalism** - Tone, structure, business appropriateness
- **Responsiveness** - Addresses original message comprehensively  
- **Clarity** - Clear, understandable communication
- **Empathy** - Emotional intelligence and human connection

---

## Benchmark Results

### Test Configuration
- **Test Model**: Mixtral (46.7B parameters)
- **Judge Models**: Mistral + Llama3.2
- **Server**: Remote Ollama (ollama.ios.htwg-konstanz.de)
- **Runtime**: 28.9 minutes for complete evaluation

### Overall Performance
- **Overall Score**: 8.70/10 🌟
- **Total Evaluations**: 80 (20 scenarios × 4 metrics)
- **Consistency**: High performance across email types

### Metric Breakdown
| Metric | Score | Strength |
|--------|-------|----------|
| Professionalism | **9.10**/10 | Excellent tone & structure |
| Responsiveness | **8.70**/10 | Addresses concerns well |
| Clarity | **8.80**/10 | Clear communication |
| Empathy | **8.30**/10 | Good emotional intelligence |

---

## Top Performing Scenarios

### Excellent Results (9.0+/10)
1. **Conference Speaking Invitation** (9.10) - Professional opportunity response
2. **Post-Training Support** (9.10) - Follow-up assistance  
3. **Project Success Celebration** (9.05) - Team achievement recognition
4. **Team Recognition** (8.97) - Employee appreciation
5. **Sales Rejection Handling** (8.93) - Professional decline

### Most Challenging (8.2-8.5/10)
- **Budget Overrun** (8.53) - Financial crisis communication
- **Vacation Request** (8.52) - HR policy navigation  
- **Conference Cancellation** (8.20) - Event change management

---

## Key Insights

### Model Strengths
- **Consistent Professional Tone** across all scenarios
- **Strong Structure** and business communication standards
- **Effective Problem-Solving** approach in responses
- **Appropriate Empathy** in sensitive situations

### Performance Patterns
- **No significant difference** between internal/external emails
- **Difficulty correlation**: Easy (8.92) > Medium (8.66) > Hard (8.64)
- **Crisis scenarios** slightly more challenging but still strong

### Dashboard Features
- **Interactive Correlation Matrix** with rotated labels
- **Detailed Response View** with expandable text
- **Multi-tab Analysis** (Overview, Metrics, Questions, Evaluators)
- **Export Capabilities** (JSON + HTML)

---

## MCP Tool Usage Benchmark

### Overview
- **Model Context Protocol (MCP)** - Tool usage evaluation framework
- **Interactive AI Assessment** - Beyond text generation to real-world capabilities
- **Tool Integration** - Weather services, mensa data, multi-tool workflows
- **Graceful Fallback** - Works even when tools are unavailable

### MCP Communication Flow

```
1. Enhanced Prompting
   User Query → Model + Tool Descriptions

2. Tool Call Generation  
   Model Response → JSON Tool Calls Extracted

3. Tool Execution
   HTTP Calls → MCP Servers → Real Data

4. Result Integration
   Tool Results → Final Response Generation
```

### Tool Usage Architecture
```python
# Tool Configuration
mcp_servers = [
    MCPServerConfig(
        name="weather",
        url="http://ollama.ios.htwg-konstanz.de:8007",
        available_tools=["get_weather", "get_forecast"]
    ),
    MCPServerConfig(
        name="mensa", 
        url="http://ollama.ios.htwg-konstanz.de:8008",
        available_tools=["get_menu", "get_daily_menu"]
    )
]

# Tool Call Format
{"tool_call": {"name": "get_weather", "parameters": {"location": "Konstanz"}}}
```

### MCP-Specific Metrics

#### Tool Usage Accuracy
```python
class ToolUsageAccuracyMetric(StandardMetric):
    def __init__(self):
        super().__init__(
            name="tool_usage_accuracy",
            evaluation_instructions="""
            Evaluate tool usage on 1-10 scale considering:
            • Tool selection appropriateness (30%)
            • Parameter accuracy (25%)
            • Result interpretation (25%)
            • Error handling (20%)
            """,
            scale_min=1, scale_max=10
        )
```

#### Information Retrieval Quality
- **Retrieval Completeness** - All necessary data collected
- **Information Relevance** - Relevant to user query  
- **Data Accuracy** - Current and reliable information
- **Synthesis** - Well-integrated final response

#### Contextual Awareness
- **Context Understanding** - Full request comprehension
- **Situational Appropriateness** - Context-appropriate responses
- **Adaptive Behavior** - Dynamic tool usage decisions
- **User Experience** - User-friendly communication

### MCP Test Scenarios

#### Dataset: 3 Tool Usage Patterns
1. **Weather Query** (Easy) - Single tool, basic usage
   - "What's the weather in Konstanz for outdoor activities?"
   - Tests: Tool selection, parameter formatting, advice generation

2. **Mensa Planning** (Medium) - Multiple calls, filtering
   - "Show me today's and tomorrow's vegetarian mensa options"
   - Tests: Multi-call coordination, dietary preference handling

3. **Event Planning** (Hard) - Multi-tool integration
   - "Plan outdoor event considering weather and mensa coordination"
   - Tests: Complex reasoning, data synthesis, comprehensive planning

### MCP Benchmark Results

#### Test Configuration
- **Test Model**: Mixtral with MCP tool capabilities
- **Judge Models**: Mistral + Llama3.2 (without tools for objective evaluation)
- **Runtime**: 3.0 minutes (faster than expected)
- **Tool Integration**: Weather + Mensa MCP servers

#### Performance Summary
- **Overall MCP Score**: 8.70/10
- **Tool Usage Accuracy**: 8.80/10
- **Information Retrieval**: 8.70/10
- **Contextual Awareness**: 8.70/10

#### Key Findings
- **Consistent Performance** across complexity levels
- **Medium complexity** scenarios performed best (8.83/10)
- **Graceful Degradation** when tools unavailable
- **Smart Fallback** to knowledge-based responses

### Technical Innovation

#### Multi-Round Tool Usage
```python
for attempt in range(max_tool_calls + 1):
    # Enhanced prompt with tool descriptions
    if tools_available and attempt == 0:
        prompt = enhance_prompt_with_tools(original_prompt)
    
    # Generate response
    response = await model.generate(prompt)
    
    # Extract and execute tool calls
    tool_calls = extract_tool_calls(response.content)
    if tool_calls:
        results = await execute_tool_calls(tool_calls)
        prompt = update_prompt_with_results(prompt, results)
```

#### Error Handling Strategy
- **Tool Server Unavailable** → Fallback to knowledge generation
- **Malformed Tool Calls** → Continue without tools
- **Tool Execution Errors** → Graceful error messaging
- **Timeout Management** → Prevent hanging requests

---

## Future Possibilities

### Extensibility
- **New Domains** - Code review, creative writing, technical docs
- **Additional Models** - Claude, GPT-4, local fine-tuned models
- **Advanced Metrics** - Factual accuracy, bias detection, safety
- **A/B Testing** - Compare different model versions

### Use Cases
- **Model Selection** - Choose best LLM for specific tasks
- **Fine-tuning Validation** - Measure improvement over base models
- **Prompt Engineering** - Optimize prompts for better performance
- **Quality Assurance** - Continuous monitoring of model outputs

---

## Conclusion

### Why This Matters
- **Objective Evaluation** - Move beyond subjective human assessment
- **Domain Expertise** - Capture specific quality requirements
- **Scalable Assessment** - Evaluate hundreds of responses efficiently
- **Actionable Insights** - Identify specific improvement areas

### Ready to Use
- **Comprehensive Framework** - Production-ready evaluation system
- **Proven Results** - Demonstrated with email response benchmark
- **Easy Extension** - Add new metrics and domains quickly
- **Rich Analysis** - Deep insights through interactive dashboards

**Email benchmark achieved 8.7/10 average** - demonstrating Mixtral's strong business communication capabilities!