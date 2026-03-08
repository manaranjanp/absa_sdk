"""
Toxicity Detection Agent (Stage 1)
------------------------------------
Screens reviews for toxic, abusive, or harmful content.
Toxic reviews are terminated — no automated response is generated.
"""

from google.adk.agents import LlmAgent


TOXICITY_INSTRUCTION = """You are the Toxicity Detection Agent in a restaurant review processing pipeline.

## Your Task
Analyze the customer review provided in the session state and determine whether it contains
toxic, abusive, or harmful content.

## Input
You will receive a review in the session state under the key `review_input`. This contains:
- review_id, restaurant_id, customer_id, review_text, review_timestamp, source_platform

## Classification Rules
- Toxicity threshold: 0.7 (scores at or above this are considered toxic)
- Distinguish between genuine frustration/strong language (e.g., "the food was damn cold") and actual abuse (hate speech, threats, harassment, severe profanity directed at people)
- Rating-only reviews with no text: pass through with toxicity_score 0.0
- Categories to check: profanity, hate_speech, threat, harassment, personal_attack

## Output Format
You MUST respond with ONLY a valid JSON object (no markdown, no explanation):
{{
  "is_toxic": false,
  "toxicity_score": 0.15,
  "toxicity_categories": [],
  "pipeline_action": "CONTINUE",
  "reasoning": "Brief explanation of classification"
}}

If toxic (score >= 0.7):
- Set "is_toxic": true
- Set "pipeline_action": "TERMINATE"
- List detected categories in "toxicity_categories"

If not toxic:
- Set "is_toxic": false
- Set "pipeline_action": "CONTINUE"

Review to analyze:
{review_input}
"""


def create_toxicity_agent(model) -> LlmAgent:
    """Create the Toxicity Detection Agent.

    Args:
        model: LiteLlm model instance for LLM calls.

    Returns:
        Configured LlmAgent for toxicity detection.
    """
    return LlmAgent(
        name="toxicity_detection_agent",
        model=model,
        instruction=TOXICITY_INSTRUCTION,
        description="Detects toxic, abusive, or harmful content in customer reviews",
        output_key="toxicity_result"
    )
