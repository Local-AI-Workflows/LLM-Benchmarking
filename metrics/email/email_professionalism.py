"""Email Professionalism Metric for email response evaluation."""

from ..metric_base import StandardMetric


class EmailProfessionalismMetric(StandardMetric):
    """Evaluates professionalism, tone, and business appropriateness of email responses."""
    
    def __init__(self):
        super().__init__(
            name="email_professionalism",
            description="Evaluates professionalism, tone, and business appropriateness of email responses",
            evaluation_instructions="""
Evaluate the professionalism of this email response on a scale of 1-10, considering:

1. TONE APPROPRIATENESS (25%):
   - Is the tone suitable for the business context?
   - Does it match the formality level of the original email?
   - Is it respectful and courteous throughout?

2. STRUCTURE AND CLARITY (25%):
   - Is the email well-structured with clear paragraphs?
   - Does it follow proper email etiquette (greeting, body, closing)?
   - Is the information organized logically?

3. BUSINESS APPROPRIATENESS (25%):
   - Is the language appropriate for business communication?
   - Are references and examples professional?
   - Does it maintain appropriate boundaries?

4. COMMUNICATION EFFECTIVENESS (25%):
   - Does it convey information clearly and efficiently?
   - Is the purpose and next steps clearly communicated?
   - Does it enhance rather than hinder business relationships?

Rate the overall professionalism from 1 (completely unprofessional) to 10 (exemplary professional communication).

Provide specific examples from the response to support your evaluation.
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on professional email standards and business communication best practices."
        ) 