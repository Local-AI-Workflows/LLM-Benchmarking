"""Tool Usage Accuracy Metric for MCP evaluation."""

from ..metric_base import StandardMetric


class ToolUsageAccuracyMetric(StandardMetric):
    """Evaluates how accurately and appropriately tools are used."""
    
    def __init__(self):
        super().__init__(
            name="tool_usage_accuracy",
            description="Evaluates accuracy and appropriateness of tool usage in MCP responses",
            evaluation_instructions="""
Evaluate the tool usage accuracy on a scale of 1-10, considering:

**CRITICAL: If the response says "I don't have real-time capabilities" or "I cannot provide current information" 
but NO TOOLS WERE USED (tool calls made: 0), this is a SEVERE FAILURE. Score must be 1-2.**

**CRITICAL: If the prompt asks for current/real-time information (like weather, news, etc.) and the metadata 
shows "Tool calls made: 0", this is also a SEVERE FAILURE. Score must be 1-3.**

1. TOOL USAGE REQUIREMENT (40%):
   - Were tools used when they SHOULD have been used?
   - If the query requires current/real-time data, were tools called?
   - Does the response claim inability when tools were available but unused?

2. TOOL SELECTION APPROPRIATENESS (20%):
   - Were the right tools chosen for the task?
   - Were unnecessary tools avoided?
   - Was tool selection logical and efficient?

3. PARAMETER ACCURACY (20%):
   - Were tool parameters correctly formatted?
   - Did parameters match the expected schema?
   - Were parameter values appropriate for the context?

4. RESULT INTERPRETATION (20%):
   - Was tool output correctly interpreted?
   - Were results properly integrated into the response?
   - Was the final answer based on tool results?

Rate the overall tool usage accuracy from 1 (completely inappropriate/incorrect tool usage or failure to use tools) 
to 10 (perfect tool selection, execution, and result integration).

**Scoring Guidelines:**
- Score 1-2: No tools used when clearly needed, response claims inability to help
- Score 3-4: Tools partially used but major issues with selection or parameters
- Score 5-6: Tools used but with some parameter issues or incomplete integration
- Score 7-8: Good tool usage with minor issues
- Score 9-10: Excellent, appropriate tool usage with correct parameters and integration

Consider:
- Whether tools were used when they should have been (MOST IMPORTANT)
- Whether tools were avoided when unnecessary
- Quality of tool interaction and result usage
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on technical correctness and appropriateness of tool usage patterns. Penalize heavily when tools are not used for queries requiring real-time data."
        )