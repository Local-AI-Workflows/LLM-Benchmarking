from ..metric_base import StandardMetric


class RobustnessMetric(StandardMetric):
    """Metric for evaluating the robustness of a response."""

    def __init__(self):
        super().__init__(
            name="robustness",
            description="Measures how well the response handles edge cases, ambiguity, and challenging inputs",
            evaluation_instructions="""Please evaluate the robustness of the response on a scale of 0-10, where:
- 0: Response fails to handle the input appropriately or breaks down completely
- 5: Response handles the input adequately but may struggle with edge cases
- 10: Response demonstrates excellent handling of challenging, ambiguous, or edge case inputs

Consider:
- Does the response handle ambiguous or unclear prompts appropriately?
- How well does it deal with edge cases or unusual inputs?
- Is the response stable and consistent in its approach?
- Does it gracefully handle limitations or uncertainty?"""
        ) 