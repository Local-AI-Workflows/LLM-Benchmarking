"""Contextual Awareness Metric for MCP evaluation."""

from ..metric_base import StandardMetric


class ContextualAwarenessMetric(StandardMetric):
    """Evaluates contextual awareness in tool usage and response generation."""
    
    def __init__(self):
        super().__init__(
            name="contextual_awareness",
            description="Evaluates contextual awareness and intelligent decision-making in MCP tool usage",
            evaluation_instructions="""
Evaluate contextual awareness on a scale of 1-10, considering:

**CRITICAL: If the query requires real-time/current information and the metadata shows "Tool calls made: 0",
this indicates POOR contextual awareness. The model failed to recognize it should use available tools. Score must be 1-4.**

1. CONTEXT UNDERSTANDING (35%):
   - Did the model understand the full context of the request?
   - Did it recognize that the query requires current/real-time information?
   - Were implicit requirements and constraints recognized?
   - Was the user's intent correctly interpreted?

2. TOOL AWARENESS (25%):
   - Did the model recognize when tools should be used?
   - Did it understand it had tools available for real-time data?
   - Did it avoid making excuses when tools could help?

3. SITUATIONAL APPROPRIATENESS (20%):
   - Were tools used appropriately for the specific situation?
   - Was the response style appropriate for the context?
   - Were temporal factors (need for current info) considered?

4. USER EXPERIENCE AWARENESS (20%):
   - Was the response user-friendly and helpful?
   - Did it provide direct answers instead of deflecting to external sources?
   - Was the information presented effectively?

Rate the overall contextual awareness from 1 (no contextual understanding) 
to 10 (excellent contextual awareness with intelligent, adaptive responses).

**Scoring Guidelines:**
- Score 1-3: Failed to recognize need for real-time data, didn't use available tools
- Score 4-5: Partial understanding but poor tool awareness
- Score 6-7: Good understanding with some tool usage issues
- Score 8-9: Strong contextual awareness with appropriate tool usage
- Score 10: Perfect understanding and tool usage

Consider:
- Understanding of explicit and implicit context
- Recognition of when real-time data is needed
- Awareness of available tools and when to use them
- Quality of adaptive decision-making
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on intelligent, context-aware decision making. Heavily penalize failure to recognize when current information is needed and tools should be used."
        )