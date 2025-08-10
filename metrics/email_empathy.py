"""
Email Empathy Metric for LLM benchmarking.

This metric evaluates the emotional intelligence, empathy, and
human-centered approach in email responses.
"""

from .metric_base import StandardMetric


class EmailEmpathyMetric(StandardMetric):
    """Evaluates the empathy and emotional intelligence shown in email responses."""
    
    def __init__(self):
        super().__init__(
            name="email_empathy",
            description="Evaluates empathy, emotional intelligence, and human-centered communication in email responses",
            evaluation_instructions="""
Evaluate the empathy and emotional intelligence of this email response on a scale of 1-10, considering:

1. EMOTIONAL AWARENESS (30%):
   - Recognizes and acknowledges the sender's emotional state or concerns
   - Shows understanding of the impact on the sender
   - Responds appropriately to underlying feelings, not just facts
   - Demonstrates awareness of emotional context

2. EMPATHETIC LANGUAGE (25%):
   - Uses language that shows care and understanding
   - Acknowledges difficulties or challenges faced by the sender
   - Expresses appropriate concern, support, or congratulations
   - Avoids dismissive or cold language

3. VALIDATION AND SUPPORT (25%):
   - Validates the sender's concerns or feelings as legitimate
   - Offers appropriate support or assistance
   - Shows willingness to help beyond the minimum required
   - Demonstrates genuine interest in the sender's wellbeing

4. RELATIONSHIP BUILDING (20%):
   - Contributes to building positive working relationships
   - Shows respect for the sender as a person
   - Maintains human warmth while being professional
   - Encourages open and continued communication

Rate the overall empathy from 1 (completely lacking empathy or emotional awareness) to 10 (demonstrates exceptional emotional intelligence and empathy).

Note: The appropriate level of empathy varies by context - professional empathy is different from personal empathy.

Provide specific examples of empathetic or non-empathetic elements in the response.
""",
            scale_min=1,
            scale_max=10,
            additional_context="Consider the appropriate level of empathy for the business context while evaluating human-centered communication."
        ) 