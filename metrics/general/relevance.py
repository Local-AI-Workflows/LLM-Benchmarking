from ..metric_base import StandardMetric


class RelevanceMetric(StandardMetric):
    """Metric for evaluating the relevance of a response to a prompt."""

    def __init__(self):
        super().__init__(
            name="relevance",
            description="Measures how well the response addresses the prompt's requirements and stays on topic",
            evaluation_instructions="""Please evaluate the relevance of the response to the prompt on a scale of 0-10, where:
- 0: Completely irrelevant or off-topic
- 5: Somewhat relevant but missing key points or going off-topic
- 10: Perfectly relevant and directly addresses all aspects of the prompt

Consider:
- Does the response address the main question or task?
- Are all parts of the prompt covered?
- Does the response stay focused on the topic?
- Is there any unnecessary or off-topic content?"""
        )
