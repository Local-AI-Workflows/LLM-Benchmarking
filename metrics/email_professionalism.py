"""
Email Professionalism Metric for LLM benchmarking.

This metric evaluates the professionalism of email responses including
tone, structure, and appropriateness for business communication.
"""

from .metric_base import StandardMetric


class EmailProfessionalismMetric(StandardMetric):
    """Evaluates the professionalism and appropriateness of email responses."""
    
    def __init__(self):
        super().__init__(
            name="email_professionalism",
            description="Evaluates professionalism, tone, and business appropriateness of email responses",
            evaluation_instructions="""
Evaluate the professionalism of this email response on a scale of 1-10, considering:

1. TONE APPROPRIATENESS (25%):
   - Professional and respectful language
   - Appropriate level of formality for the context
   - Empathetic where needed, assertive where appropriate
   - No overly casual or unprofessional language

2. STRUCTURE AND CLARITY (25%):
   - Clear and well-organized content
   - Proper email etiquette (greeting, body, closing)
   - Logical flow of information
   - Appropriate length and conciseness

3. BUSINESS APPROPRIATENESS (25%):
   - Suitable for the business context
   - Demonstrates understanding of professional relationships
   - Avoids inappropriate personal details
   - Uses business-appropriate language and references

4. COMMUNICATION EFFECTIVENESS (25%):
   - Addresses all key points from the original message
   - Clear call-to-action or next steps where appropriate
   - Demonstrates active listening and understanding
   - Facilitates productive ongoing communication

Rate the overall professionalism from 1 (completely unprofessional) to 10 (exemplary professional communication).

Provide specific examples from the response to support your evaluation.
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on professional email standards and business communication best practices."
        ) 