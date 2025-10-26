"""Tool Selection Efficiency Metric for MCP evaluation."""

from ..metric_base import StandardMetric


class ToolSelectionEfficiencyMetric(StandardMetric):
    """Evaluates efficiency and appropriateness of tool selection strategy."""
    
    def __init__(self):
        super().__init__(
            name="tool_selection_efficiency",
            description="Evaluates efficiency of tool selection and minimal tool usage strategy",
            evaluation_instructions="""
Evaluate the tool selection efficiency on a scale of 1-10, considering:

**CRITICAL: If the query requires tools but metadata shows "Tool calls made: 0", this is the WORST 
efficiency - the model chose zero tools when at least one was needed. Score must be 1-2.**

**CRITICAL: Using zero tools when tools are needed is LESS efficient than using appropriate tools.**

1. APPROPRIATE TOOL COUNT (35%):
   - Were enough tools used to answer the query?
   - Was the tool count appropriate (0 is bad if tools needed, 10 is bad if only 1 needed)?
   - Were redundant tool calls avoided while still getting necessary data?

2. TOOL SELECTION LOGIC (30%):
   - Were the most appropriate tools selected?
   - Was the tool selection order logical and efficient?
   - Did the model choose relevant tools for the task?

3. EXECUTION EFFICIENCY (20%):
   - Was the minimum necessary number of tools used (but not zero when tools needed)?
   - Were expensive operations avoided when simpler ones sufficed?
   - Was the tool usage sequence optimized?

4. GOAL ACHIEVEMENT (15%):
   - Did the tool usage strategy achieve the goal?
   - Was the result complete?
   - Was quality maintained while being efficient?

Rate the overall tool selection efficiency from 1 (completely wrong tool count or selection) 
to 10 (optimal tool selection achieving complete results).

**Scoring Guidelines:**
- Score 1-2: Zero tools used when tools are required (worst efficiency)
- Score 3-4: Too many or wrong tools selected
- Score 5-6: Correct tools but inefficient sequence or redundancy
- Score 7-8: Good tool selection with minor inefficiencies
- Score 9-10: Optimal tool selection and usage

Consider:
- Did the model use the RIGHT NUMBER of tools (not zero when needed)?
- Was the tool selection strategy appropriate for the query?
- Was efficiency balanced with completeness?
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on appropriate tool selection. Using zero tools when they're needed is the least efficient choice possible."
        )

