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

1. CONTEXT UNDERSTANDING (30%):
   - Did the model understand the full context of the request?
   - Were implicit requirements and constraints recognized?
   - Was the user's intent correctly interpreted?

2. SITUATIONAL APPROPRIATENESS (25%):
   - Were tools used appropriately for the specific situation?
   - Was the response style appropriate for the context?
   - Were cultural, temporal, or domain-specific factors considered?

3. ADAPTIVE BEHAVIOR (25%):
   - Did the model adapt tool usage based on context?
   - Were fallback strategies employed when needed?
   - Was tool selection dynamic and context-driven?

4. USER EXPERIENCE AWARENESS (20%):
   - Was the response user-friendly and accessible?
   - Were complex technical details handled appropriately?
   - Was the information presented at the right level of detail?

Rate the overall contextual awareness from 1 (no contextual understanding) 
to 10 (excellent contextual awareness with intelligent, adaptive responses).

Consider:
- Understanding of explicit and implicit context
- Appropriateness of tool usage for the situation
- Quality of adaptive decision-making
- User experience and communication effectiveness
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on intelligent, context-aware decision making and user experience."
        ) 