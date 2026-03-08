"""
Response Generation Agent (Stage 5)
--------------------------------------
Composes a personalized, brand-consistent response to the customer
review based on all preceding analysis.
"""

import os
from google.adk.agents import LlmAgent


def _load_brand_guidelines() -> str:
    """Load brand voice guidelines for injection into instructions."""
    guide_path = os.path.join(os.path.dirname(__file__), "..", "data", "brand_voice_guidelines.md")
    try:
        with open(guide_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Use a warm, professional, and empathetic tone."


RESPONSE_GENERATION_INSTRUCTION = """You are the Response Generation Agent in a restaurant review processing pipeline.

## Your Task
Compose a personalized, brand-consistent response to the customer review.
Your response will be validated by the Output Guardrail Agent before publishing.

## Prerequisite
Check the toxicity result: {toxicity_result}
If pipeline_action is "TERMINATE", respond with:
{{"response_text": "", "pipeline_action": "TERMINATE", "reason": "Toxic review — no response generated"}}

## Input
- Review: {review_input}
- Aspects: {aspect_result}
- Sentiments: {sentiment_result}
- Escalation: {escalation_result}

## Brand Voice Guidelines
""" + _load_brand_guidelines() + """

## Response Rules
1. Address every negative aspect specifically — never ignore or gloss over complaints
2. For negative aspects: acknowledge → apologize → provide concrete next step
3. Acknowledge positives with genuine gratitude
4. If an escalation ticket was created, inform the customer that someone will reach out
   (include approximate timeframe based on SLA, but don't mention the ticket system)
5. Personalize: use customer name if available, reference specific review details
6. Maximum 300 words
7. NEVER disclose: sentiment scores, toxicity classifications, customer tier,
   policy triggers, or any system-internal data
8. Sign off with: "Warm regards, The [Restaurant] Team"

## Output Format
Respond with ONLY a valid JSON object:
{{
  "response_text": "Dear Sarah, thank you for sharing your wonderful experience...",
  "word_count": 150,
  "aspects_addressed": ["FOOD_QUALITY", "SERVICE", "AMBIANCE"],
  "callback_mentioned": false,
  "pipeline_action": "CONTINUE"
}}
"""


def create_response_generation_agent(model) -> LlmAgent:
    """Create the Response Generation Agent.

    Args:
        model: LiteLlm model instance for LLM calls.

    Returns:
        Configured LlmAgent for generating customer-facing responses.
    """
    return LlmAgent(
        name="response_generation_agent",
        model=model,
        instruction=RESPONSE_GENERATION_INSTRUCTION,
        description="Generates personalized, brand-consistent responses to customer reviews",
        output_key="response_result"
    )
