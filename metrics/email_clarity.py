"""
Email Clarity Metric for LLM benchmarking.

This metric evaluates the clarity, understandability, and effectiveness
of communication in email responses.
"""

from .metric_base import StandardMetric


class EmailClarityMetric(StandardMetric):
    """Evaluates the clarity and understandability of email responses."""
    
    def __init__(self):
        super().__init__(
            name="email_clarity",
            description="Evaluates clarity, understandability, and communication effectiveness of email responses",
            evaluation_instructions="""
Evaluate the clarity of this email response on a scale of 1-10, considering:

1. LANGUAGE CLARITY (30%):
   - Uses clear, simple language appropriate for the audience
   - Avoids unnecessary jargon or complex terms
   - Sentences are well-structured and easy to follow
   - Grammar and word choice support understanding

2. INFORMATION ORGANIZATION (25%):
   - Information is logically organized and easy to follow
   - Uses appropriate formatting (paragraphs, bullets, etc.)
   - Key points are easy to identify and distinguish
   - Flow from one point to another is smooth and logical

3. CONCISENESS AND FOCUS (25%):
   - Gets to the point without unnecessary wordiness
   - Stays focused on relevant information
   - Balances completeness with brevity
   - Eliminates redundant or confusing elements

4. ACTIONABILITY (20%):
   - Clear about what actions are needed, if any
   - Specific rather than vague instructions or requests
   - Easy to understand what the recipient should do next
   - Removes ambiguity about responsibilities and timelines

Rate the overall clarity from 1 (completely unclear and confusing) to 10 (perfectly clear and easy to understand).

Provide specific examples of clear or unclear elements in the response.
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on how easily the intended recipient could understand and act on the message."
        ) 