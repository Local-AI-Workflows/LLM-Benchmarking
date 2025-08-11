from ..metric_base import StandardMetric


class HallucinationsMetric(StandardMetric):
    """Metric for evaluating the presence of hallucinations in a response."""

    def __init__(self):
        super().__init__(
            name="hallucinations",
            description="Measures the extent to which the response contains fabricated or incorrect information",
            evaluation_instructions="""Please evaluate the presence of hallucinations in the response on a scale of 0-10, where:
- 0: Response contains many clear hallucinations or completely fabricated information
- 5: Response contains some potential hallucinations or uncertain information
- 10: Response contains no hallucinations and all information appears to be accurate

Consider:
- Are there any factual claims that are clearly false?
- Does the response make up specific details that cannot be verified?
- Are there any contradictions within the response?
- Does the response present speculation as fact?"""
        ) 