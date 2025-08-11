"""Email Clarity Metric for email response evaluation."""

from ..metric_base import StandardMetric


class EmailClarityMetric(StandardMetric):
    """Evaluates the clarity and understandability of email responses."""
    
    def __init__(self):
        super().__init__(
            name="email_clarity",
            description="Evaluates the clarity and understandability of email responses",
            evaluation_instructions="""
Evaluate the clarity of this email response on a scale of 1-10, considering:

1. LANGUAGE CLARITY (30%):
   - Is the language clear and easy to understand?
   - Are sentences well-constructed and grammatically correct?
   - Is jargon or technical terms explained appropriately?

2. INFORMATION ORGANIZATION (25%):
   - Is the information presented in a logical order?
   - Are key points highlighted or emphasized effectively?
   - Is the structure easy to follow?

3. CONCISENESS AND FOCUS (25%):
   - Is the message appropriately concise without being too brief?
   - Does it stay focused on the relevant topics?
   - Is unnecessary information avoided?

4. ACTIONABILITY (20%):
   - Are action items or next steps clearly stated?
   - Is it clear what the recipient needs to do (if anything)?
   - Are deadlines or timelines clearly communicated?

Rate the overall clarity from 1 (very confusing and unclear) 
to 10 (crystal clear and easy to understand).

Consider whether the recipient would clearly understand the message and any required actions.
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on how easily the recipient can understand and act on the message."
        ) 