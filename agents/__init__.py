"""
ABSA Agent Modules
-------------------
Factory functions for creating each subagent in the ABSA pipeline.
Each module exports a create_*_agent(model) function.
"""

from agents.toxicity_agent import create_toxicity_agent
from agents.aspect_extraction_agent import create_aspect_extraction_agent
from agents.sentiment_analysis_agent import create_sentiment_analysis_agent
from agents.policy_escalation_agent import create_policy_escalation_agent
from agents.response_generation_agent import create_response_generation_agent
from agents.output_guardrail_agent import create_output_guardrail_agent

__all__ = [
    "create_toxicity_agent",
    "create_aspect_extraction_agent",
    "create_sentiment_analysis_agent",
    "create_policy_escalation_agent",
    "create_response_generation_agent",
    "create_output_guardrail_agent",
]
