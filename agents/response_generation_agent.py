"""Response Generation Agent (Stage 5)"""

import os
from google.adk.agents import LlmAgent


def _load_brand_guidelines() -> str:
    guide_path = os.path.join(os.path.dirname(__file__), "..", "data", "brand_voice_guidelines.md")
    try:
        with open(guide_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Use a warm, professional, and empathetic tone."


RESPONSE_GENERATION_INSTRUCTION = """Compose a personalized response to the customer review.

Input:
- Review: {review_input}
- Aspects: {aspect_result}
- Sentiments: {sentiment_result}
- Escalation: {escalation_result}

## Brand Voice Guidelines
""" + _load_brand_guidelines() + """

## Rules
1. Address every negative aspect: acknowledge -> apologize -> concrete next step
2. Acknowledge positives with genuine gratitude
3. If escalation ticket was created, mention someone will reach out (with timeframe based on SLA) but don't mention the ticket system
4. Use customer name if available, reference specific review details
5. Maximum 300 words
6. NEVER disclose: sentiment scores, toxicity results, customer tier, or system internals
7. Sign off: "Warm regards, The [Restaurant] Team"

Respond with ONLY this JSON:
{{
  "response_text": "Dear Sarah, thank you for sharing your wonderful experience..."
}}
"""


def create_response_generation_agent(model) -> LlmAgent:
    return LlmAgent(
        name="response_generation_agent",
        model=model,
        instruction=RESPONSE_GENERATION_INSTRUCTION,
        description="Generates personalized responses to customer reviews",
        output_key="response_result",
    )
