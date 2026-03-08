"""Sentiment Analysis Agent (Stage 3)"""

from google.adk.agents import LlmAgent


SENTIMENT_ANALYSIS_INSTRUCTION = """Classify sentiment for each extracted aspect. A single review can be positive on one aspect and negative on another.

Sentiment scale:
- VERY_POSITIVE: 0.6 to 1.0
- POSITIVE: 0.2 to 0.59
- NEUTRAL: -0.19 to 0.19
- NEGATIVE: -0.59 to -0.2
- VERY_NEGATIVE: -1.0 to -0.6

Handle negation ("not good" -> NEGATIVE), sarcasm, and conditional sentiment ("would have been great if..." -> NEGATIVE).

Input:
- Review: {review_input}
- Aspects: {aspect_result}

Respond with ONLY this JSON:
{{
  "aspect_sentiments": [
    {{
      "aspect_code": "FOOD_QUALITY",
      "sentiment_label": "POSITIVE",
      "sentiment_score": 0.75
    }}
  ],
  "overall_sentiment": "POSITIVE",
  "overall_sentiment_score": 0.65
}}
"""


def create_sentiment_analysis_agent(model) -> LlmAgent:
    return LlmAgent(
        name="sentiment_analysis_agent",
        model=model,
        instruction=SENTIMENT_ANALYSIS_INSTRUCTION,
        description="Classifies sentiment per extracted aspect",
        output_key="sentiment_result",
    )
