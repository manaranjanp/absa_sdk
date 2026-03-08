"""
Policy Evaluation & Escalation Agent (Stage 4)
-------------------------------------------------
Evaluates sentiment results against simple threshold rules.
Creates escalation tickets for eligible customers based on their tier.
"""

from google.adk.agents import LlmAgent
from agents.escalation_tools import create_escalation_ticket


POLICY_ESCALATION_INSTRUCTION = """You are the Policy Evaluation & Escalation Agent in a restaurant review processing pipeline.

## Your Task
Evaluate the sentiment results against the rules below.
Raise notifications when thresholds are breached and create escalation tickets
for eligible customers based on their loyalty tier.

## Prerequisite
Check the toxicity result: {toxicity_result}
If pipeline_action is "TERMINATE", respond with:
{{"notifications": [], "escalation_ticket": null, "pipeline_action": "TERMINATE"}}

## Input
- Review metadata: {review_input}
- Sentiment results: {sentiment_result}

## Notification Rules
If any aspect has a sentiment_score below -0.5, raise a notification for that aspect.

## Escalation Rules
Determine customer tier from review metadata (customer_tier field).
Apply the matching tier rule:
- Platinum: Any negative aspect → HIGH priority, 4h SLA
- Gold: Overall sentiment NEGATIVE or worse → MEDIUM priority, 24h SLA
- Silver: Overall sentiment VERY_NEGATIVE → LOW priority, 48h SLA
- Standard: No ticket

If escalation is needed, call `create_escalation_ticket` with the required parameters.

## Output Format
Respond with ONLY a valid JSON object:
{{
  "notifications": [
    {{
      "aspect_code": "SERVICE",
      "sentiment_score": -0.7,
      "message": "Sentiment score below threshold for SERVICE"
    }}
  ],
  "escalation_ticket": {{
    "ticket_id": 1,
    "action": "CREATED",
    "priority": "HIGH",
    "sla_hours": 4
  }},
  "pipeline_action": "CONTINUE"
}}

If no escalation needed, set "escalation_ticket": null.
"""


def create_policy_escalation_agent(model) -> LlmAgent:
    """Create the Policy Evaluation & Escalation Agent.

    Args:
        model: LiteLlm model instance for LLM calls.

    Returns:
        Configured LlmAgent with escalation tool.
    """
    return LlmAgent(
        name="policy_escalation_agent",
        model=model,
        instruction=POLICY_ESCALATION_INSTRUCTION,
        description="Evaluates policies, fires alerts, and creates escalation tickets",
        tools=[create_escalation_ticket],
        output_key="escalation_result"
    )
