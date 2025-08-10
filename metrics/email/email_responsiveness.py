"""Email Responsiveness Metric for email response evaluation."""

from ..metric_base import StandardMetric


class EmailResponsivenessMetric(StandardMetric):
    """Evaluates how comprehensively and appropriately the response addresses the original message."""
    
    def __init__(self):
        super().__init__(
            name="email_responsiveness",
            description="Evaluates how comprehensively and appropriately the response addresses the original message",
            evaluation_instructions="""
Evaluate the responsiveness of this email response on a scale of 1-10, considering:

1. COMPLETENESS OF RESPONSE (30%):
   - Does it address all the key points raised in the original email?
   - Are all questions answered thoroughly?
   - Is important information or context missing?

2. APPROPRIATENESS OF RESPONSE (25%):
   - Is the response appropriate for the specific situation?
   - Does it match the urgency and importance of the original message?
   - Is the level of detail appropriate?

3. PROBLEM-SOLVING ORIENTATION (25%):
   - Does it provide solutions or next steps where needed?
   - Are practical recommendations offered?
   - Does it move the conversation forward constructively?

4. TIMELINESS AND FOLLOW-UP (20%):
   - Does it address timing concerns appropriately?
   - Are follow-up actions or timelines clearly communicated?
   - Is there awareness of urgency where applicable?

Rate the overall responsiveness from 1 (completely unresponsive to original concerns) 
to 10 (perfectly addresses all aspects of the original message).

Consider whether the sender's needs and concerns are fully understood and addressed.
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on how well the response serves the original sender's needs and concerns."
        ) 