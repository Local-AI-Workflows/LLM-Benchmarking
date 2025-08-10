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

1. TOOL SELECTION APPROPRIATENESS (30%):
   - Were the right tools chosen for the task?
   - Were unnecessary tools avoided?
   - Was tool selection logical and efficient?

2. PARAMETER ACCURACY (25%):
   - Were tool parameters correctly formatted?
   - Did parameters match the expected schema?
   - Were parameter values appropriate for the context?

3. RESULT INTERPRETATION (25%):
   - Was tool output correctly interpreted?
   - Were results properly integrated into the response?
   - Was the final answer based on tool results?

4. ERROR HANDLING (20%):
   - Were tool errors handled gracefully?
   - Was appropriate fallback behavior demonstrated?
   - Were error messages communicated clearly?

Rate the overall tool usage accuracy from 1 (completely inappropriate/incorrect tool usage) 
to 10 (perfect tool selection, execution, and result integration).

Consider:
- Whether tools were used when they should have been
- Whether tools were avoided when unnecessary
- Quality of tool interaction and result usage
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on technical correctness and appropriateness of tool usage patterns."
        ) 