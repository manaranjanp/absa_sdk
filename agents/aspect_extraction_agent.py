"""Aspect Extraction Agent (Stage 2)"""

from google.adk.agents import LlmAgent


ASPECT_EXTRACTION_INSTRUCTION = """Extract all restaurant experience aspects mentioned in the review. Map each to one of these codes:

- FOOD_QUALITY: taste, freshness, portion, cooking, ingredients, flavor, temperature
- SERVICE: staff, waiter, server, attentive, slow, rude, manager
- AMBIANCE: decor, noise, lighting, vibe, atmosphere, music, seating
- CLEANLINESS: clean, dirty, filthy, restroom, hygiene, sticky

Extract both explicit ("the food was great") and implicit ("it was filthy in there" -> CLEANLINESS) mentions.

Respond with ONLY this JSON:
{{
  "aspects": [
    {{
      "aspect_code": "FOOD_QUALITY",
      "mention_text": "the grilled salmon"
    }}
  ]
}}

Review:
{review_input}
"""


def create_aspect_extraction_agent(model) -> LlmAgent:
    return LlmAgent(
        name="aspect_extraction_agent",
        model=model,
        instruction=ASPECT_EXTRACTION_INSTRUCTION,
        description="Extracts restaurant experience aspects from reviews",
        output_key="aspect_result",
    )
