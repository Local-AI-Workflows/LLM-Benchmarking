"""
Email Responsiveness Metric for LLM benchmarking.

This metric evaluates how well the email response addresses the original
message concerns, questions, and requirements.
"""

from .metric_base import StandardMetric


class EmailResponsivenessMetric(StandardMetric):
    """Evaluates how well the email response addresses the original message concerns."""
    
    def __init__(self):
        super().__init__(
            name="email_responsiveness",
            description="Evaluates how comprehensively and appropriately the response addresses the original message",
            evaluation_instructions="""
Evaluate how well this email response addresses the original message on a scale of 1-10, considering:

1. COMPLETENESS OF RESPONSE (30%):
   - Addresses all questions or concerns raised
   - Acknowledges all key points from the original message
   - Provides necessary information or explanations
   - No important aspects are ignored or overlooked

2. APPROPRIATENESS OF RESPONSE (25%):
   - Response matches the urgency and importance of the original message
   - Tone and approach are suitable for the situation
   - Level of detail is appropriate for the context
   - Response type matches what was requested or needed

3. PROBLEM-SOLVING ORIENTATION (25%):
   - Offers solutions or alternatives where appropriate
   - Shows initiative in addressing underlying issues
   - Provides actionable next steps
   - Demonstrates helpful and constructive approach

4. TIMELINESS AND FOLLOW-UP (20%):
   - Acknowledges time-sensitive elements appropriately
   - Provides clear timelines or expectations
   - Sets up appropriate follow-up mechanisms
   - Demonstrates understanding of urgency levels

Rate the overall responsiveness from 1 (completely unresponsive to original concerns) to 10 (perfectly addresses all aspects of the original message).

Provide specific examples of how the response does or doesn't address key elements from the original message.
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on how well the response serves the sender's needs and addresses their specific concerns."
        ) 