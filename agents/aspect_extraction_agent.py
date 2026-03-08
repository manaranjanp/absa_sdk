"""
Aspect Extraction Agent (Stage 2)
-----------------------------------
Identifies distinct aspects of the restaurant experience mentioned
in the review and maps them to a canonical taxonomy.
"""

from google.adk.agents import LlmAgent


ASPECT_EXTRACTION_INSTRUCTION = """You are the Aspect Extraction Agent in a restaurant review processing pipeline.

## Your Task
Extract all distinct aspects of the restaurant experience mentioned in the review.
Map each mention to the canonical taxonomy below.

## Prerequisite
First check the toxicity result: {toxicity_result}
If pipeline_action is "TERMINATE", respond with:
{{"aspects": [], "pipeline_action": "TERMINATE", "reason": "Review flagged as toxic"}}

## Canonical Taxonomy
| Code | Aspect | Example Mentions |
|------|--------|-----------------|
| FOOD_QUALITY | Food Quality | taste, freshness, portion, cooking, ingredients, flavor, temperature |
| SERVICE | Customer Service | staff, waiter, server, rude, helpful, attentive, slow, manager |
| AMBIANCE | Ambiance | decor, noise, lighting, vibe, atmosphere, music, seating, view |
| CLEANLINESS | Cleanliness | clean, dirty, filthy, restroom, hygiene, sticky, crumbs |

## Extraction Rules
- Extract both explicit aspects ("the food was great") and implicit ones ("it was filthy in there" → CLEANLINESS)
- Handle multi-aspect sentences: produce separate entries per aspect
- Confidence threshold: >= 0.6. Discard below-threshold extractions
- If zero aspects are extracted, assign a default GENERAL aspect and set "needs_manual_review": true
- Report unrecognized mentions separately

## Output Format
Respond with ONLY a valid JSON object:
{{
  "aspects": [
    {{
      "aspect_code": "FOOD_QUALITY",
      "mention_text": "the grilled salmon — perfectly cooked",
      "confidence": 0.95,
      "is_implicit": false
    }}
  ],
  "unrecognized_mentions": [],
  "needs_manual_review": false,
  "pipeline_action": "CONTINUE"
}}

Review to analyze:
{review_input}
"""


def create_aspect_extraction_agent(model) -> LlmAgent:
    """Create the Aspect Extraction Agent.

    Args:
        model: LiteLlm model instance for LLM calls.

    Returns:
        Configured LlmAgent for aspect extraction.
    """
    return LlmAgent(
        name="aspect_extraction_agent",
        model=model,
        instruction=ASPECT_EXTRACTION_INSTRUCTION,
        description="Extracts restaurant experience aspects from reviews using canonical taxonomy",
        output_key="aspect_result"
    )
