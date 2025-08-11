"""Email Empathy Metric for email response evaluation."""

from ..metric_base import StandardMetric


class EmailEmpathyMetric(StandardMetric):
    """Evaluates the empathy and emotional intelligence shown in email responses."""
    
    def __init__(self):
        super().__init__(
            name="email_empathy",
            description="Evaluates the empathy and emotional intelligence shown in email responses",
            evaluation_instructions="""
Evaluate the empathy and emotional intelligence of this email response on a scale of 1-10, considering:

1. EMOTIONAL AWARENESS (30%):
   - Does the response recognize the emotional context of the original message?
   - Is there awareness of the sender's feelings or situation?
   - Are emotional cues appropriately acknowledged?

2. EMPATHETIC LANGUAGE (25%):
   - Is the language warm and understanding where appropriate?
   - Does it show genuine concern for the sender's situation?
   - Is the tone supportive and non-judgmental?

3. VALIDATION AND SUPPORT (25%):
   - Are the sender's concerns or feelings validated?
   - Is appropriate reassurance or support offered?
   - Does it demonstrate understanding of the human impact?

4. RELATIONSHIP BUILDING (20%):
   - Does the response strengthen rather than damage the relationship?
   - Is it considerate of the ongoing professional relationship?
   - Does it show care for the person behind the business interaction?

Rate the overall empathy from 1 (completely cold and insensitive) 
to 10 (highly empathetic and emotionally intelligent).

Consider whether the response shows genuine human understanding and care while maintaining professionalism.
""",
            scale_min=1,
            scale_max=10,
            additional_context="Focus on emotional intelligence and human-centered communication while maintaining business appropriateness."
        ) 