"""Toxicity Detection Agent (Stage 1)"""

from google.adk.agents import LlmAgent


TOXICITY_INSTRUCTION = """Analyze the customer review for toxic, abusive, or harmful content.

Distinguish genuine frustration ("the food was damn cold") from actual abuse (hate speech, threats, harassment, personal attacks).

Toxicity threshold: 0.7. Scores >= 0.7 are toxic.

Respond with ONLY this JSON:
{{
  "is_toxic": false,
  "toxicity_score": 0.15
}}

Review:
{review_input}
"""


def create_toxicity_agent(model) -> LlmAgent:
    return LlmAgent(
        name="toxicity_detection_agent",
        model=model,
        instruction=TOXICITY_INSTRUCTION,
        description="Detects toxic or abusive content in customer reviews",
        output_key="toxicity_result",
    )
