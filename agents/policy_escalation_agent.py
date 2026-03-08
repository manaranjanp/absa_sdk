"""Policy Evaluation & Escalation Agent (Stage 4)"""

from google.adk.agents import LlmAgent
from agents.escalation_tools import create_escalation_ticket


POLICY_ESCALATION_INSTRUCTION = """Evaluate sentiment results and create escalation tickets when the score is negative.

Input:
- Review metadata: {review_input}
- Sentiment results: {sentiment_result}

## Rule
Call the `create_escalation_ticket` tool ONLY if overall_sentiment_score < -0.3.

Use priority="HIGH" and sla_hours=4 if score < -0.6, otherwise priority="MEDIUM" and sla_hours=24.

Do NOT call the tool if overall_sentiment_score >= -0.3.

After deciding, respond with ONLY this JSON:
{{
  "escalation_ticket": {{
    "priority": "HIGH",
    "sla_hours": 4
  }}
}}

If no escalation needed:
{{
  "escalation_ticket": null
}}
"""


def create_policy_escalation_agent(model) -> LlmAgent:
    return LlmAgent(
        name="policy_escalation_agent",
        model=model,
        instruction=POLICY_ESCALATION_INSTRUCTION,
        description="Creates escalation tickets based on sentiment thresholds and customer tier",
        tools=[create_escalation_ticket],
        output_key="escalation_result",
    )
