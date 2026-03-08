"""Output Guardrail Agent (Stage 6)"""

from google.adk.agents import LlmAgent


OUTPUT_GUARDRAIL_INSTRUCTION = """Validate the generated response before publishing.

Input:
- Review: {review_input}
- Aspects & sentiments: {aspect_result}, {sentiment_result}
- Escalation: {escalation_result}
- Response: {response_result}

## Rules (check ALL)
1. Tone: empathetic for complaints, warm for praise. No passive-aggressive or dismissive language.
2. Safety: no profanity, inflammatory language, or legally liable statements.
3. Completeness: every negative aspect must be addressed. No complaints skipped.
4. Length: within 300 words.

Rules 1-3 are CRITICAL (block publishing). Rule 4 is WARNING (flag but may pass).

Respond with ONLY this JSON:

If passed:
{{
  "guardrail_passed": true,
  "guardrail_action": "PUBLISH",
  "violations": []
}}

If failed:
{{
  "guardrail_passed": false,
  "guardrail_action": "REVISE",
  "violations": ["Completeness: SERVICE aspect not addressed"]
}}

guardrail_action: PUBLISH, REVISE, or ESCALATE_TO_HUMAN
"""


def create_output_guardrail_agent(model) -> LlmAgent:
    return LlmAgent(
        name="output_guardrail_agent",
        model=model,
        instruction=OUTPUT_GUARDRAIL_INSTRUCTION,
        description="Validates responses against guardrail rules before publishing",
        output_key="guardrail_result",
    )
