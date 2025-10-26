"""Information Retrieval Quality Metric for MCP evaluation."""

from ..metric_base import StandardMetric


class InformationRetrievalQualityMetric(StandardMetric):
    """Evaluates quality of information retrieval and integration."""
    
    def __init__(self):
        super().__init__(
            name="information_retrieval_quality", 
            description="Evaluates quality of information retrieval and integration in MCP responses",
            evaluation_instructions="""
Evaluate information retrieval quality on a scale of 1-10, considering:

**CRITICAL: If the metadata shows "Tool calls made: 0" and the response does NOT contain specific, 
current information (just general advice or disclaimers), this is a RETRIEVAL FAILURE. Score must be 1-3.**

**CRITICAL: If the response says to "check a website" or "use an app" instead of providing the 
information directly through tools, this is a FAILURE. Score must be 1-2.**

1. RETRIEVAL COMPLETENESS (30%):
   - Was all necessary information actually retrieved?
   - Were tools used to get current/real-time data when needed?
   - Was the information complete and sufficient to answer the query?

2. INFORMATION RELEVANCE (25%):
   - Was retrieved information directly relevant to the question?
   - Were irrelevant details filtered out appropriately?
   - Was the information depth appropriate for the question?

3. DATA FRESHNESS & ACCURACY (25%):
   - Was current/up-to-date information retrieved when needed?
   - Were tools actually called to get fresh data?
   - Is the information specific (e.g., actual temperature) or vague (e.g., "check a website")?

4. SYNTHESIS & INTEGRATION (20%):
   - Was retrieved information well-integrated into the response?
   - Were multiple sources synthesized coherently?
   - Was the final answer comprehensive yet concise?

Rate the overall information retrieval quality from 1 (poor/incomplete retrieval or no retrieval) 
to 10 (excellent retrieval and integration of relevant, accurate, current information).

**Scoring Guidelines:**
- Score 1-2: No actual information retrieval, just suggestions to check elsewhere
- Score 3-4: Minimal retrieval, vague or outdated information
- Score 5-6: Some information retrieved but incomplete or not well integrated
- Score 7-8: Good retrieval with current information and decent integration
- Score 9-10: Excellent retrieval with fresh, accurate data perfectly integrated

Consider:
- Whether ANY information was actually retrieved (not just suggested)
- How well information was integrated into the response
- Currency and specificity of the information (exact numbers vs. general advice)
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on information quality, relevance, and effective integration. Heavily penalize responses that don't actually retrieve information when tools are available."
        )