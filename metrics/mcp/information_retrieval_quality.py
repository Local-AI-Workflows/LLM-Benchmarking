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

1. RETRIEVAL COMPLETENESS (25%):
   - Was all necessary information retrieved?
   - Were multiple relevant sources consulted when appropriate?
   - Was the search strategy comprehensive?

2. INFORMATION RELEVANCE (25%):
   - Was retrieved information directly relevant to the question?
   - Were irrelevant details filtered out appropriately?
   - Was the information depth appropriate for the question?

3. DATA FRESHNESS & ACCURACY (25%):
   - Was current/up-to-date information retrieved when needed?
   - Were data sources reliable and authoritative?
   - Was information cross-verified when appropriate?

4. SYNTHESIS & INTEGRATION (25%):
   - Was retrieved information well-integrated into the response?
   - Were multiple sources synthesized coherently?
   - Was the final answer comprehensive yet concise?

Rate the overall information retrieval quality from 1 (poor/incomplete retrieval) 
to 10 (excellent retrieval and integration of relevant, accurate information).

Consider:
- Whether the right information was retrieved
- How well information was integrated into the response
- Quality and reliability of the information sources
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on information quality, relevance, and effective integration into responses."
        ) 