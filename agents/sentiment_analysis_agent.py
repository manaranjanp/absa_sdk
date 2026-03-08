"""
Sentiment Analysis Agent (Stage 3)
-------------------------------------
Classifies sentiment toward each extracted aspect independently.
A single review may be positive on one aspect and negative on another.
"""

from google.adk.agents import LlmAgent


SENTIMENT_ANALYSIS_INSTRUCTION = """You are the Sentiment Analysis Agent in a restaurant review processing pipeline.

## Your Task
Classify the sentiment toward each extracted aspect from the previous stage.
A single review can be positive on one aspect and negative on another.

## Prerequisite
Check the toxicity result: {toxicity_result}
If pipeline_action is "TERMINATE", respond with:
{{"aspect_sentiments": [], "pipeline_action": "TERMINATE"}}

## Input
- Original review: {review_input}
- Extracted aspects: {aspect_result}

## Sentiment Labels & Scores
| Label | Score Range |
|-------|------------|
| VERY_POSITIVE | 0.6 to 1.0 |
| POSITIVE | 0.2 to 0.59 |
| NEUTRAL | -0.19 to 0.19 |
| NEGATIVE | -0.59 to -0.2 |
| VERY_NEGATIVE | -1.0 to -0.6 |

## Analysis Rules
- Handle negation: "not good" → NEGATIVE
- Handle sarcasm: "Oh sure, the food was AMAZING" (with negative context) → NEGATIVE
- Handle conditional sentiment: "would have been great if it weren't cold" → NEGATIVE
- Include the supporting text span for each classification
- Compute overall_sentiment as a weighted average (equal weights by default)

## Output Format
Respond with ONLY a valid JSON object:
{{
  "aspect_sentiments": [
    {{
      "aspect_code": "FOOD_QUALITY",
      "sentiment_label": "POSITIVE",
      "sentiment_score": 0.75,
      "confidence": 0.9,
      "supporting_text": "the grilled salmon — perfectly cooked"
    }}
  ],
  "overall_sentiment": "POSITIVE",
  "overall_sentiment_score": 0.65,
  "pipeline_action": "CONTINUE"
}}
"""


def create_sentiment_analysis_agent(model) -> LlmAgent:
    """Create the Sentiment Analysis Agent.

    Args:
        model: LiteLlm model instance for LLM calls.

    Returns:
        Configured LlmAgent for per-aspect sentiment classification.
    """
    return LlmAgent(
        name="sentiment_analysis_agent",
        model=model,
        instruction=SENTIMENT_ANALYSIS_INSTRUCTION,
        description="Classifies sentiment per extracted aspect with scores and labels",
        output_key="sentiment_result"
    )
