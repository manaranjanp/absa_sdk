"""Pipeline callbacks for conditional flow control."""

import json
import os
from datetime import datetime
from google.genai import types

HUMAN_REVIEW_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "human_review_queue.json"
)


def check_toxicity_before_agent(callback_context):
    """Skip remaining agents if the review was flagged as toxic.

    Used as before_agent_callback on stages 2-6.
    Returns Content to skip the agent if toxic, None to proceed normally.
    """
    state = callback_context.state
    toxicity_raw = state.get("toxicity_result", "{}")

    try:
        toxicity = json.loads(toxicity_raw) if isinstance(toxicity_raw, str) else toxicity_raw
    except (json.JSONDecodeError, TypeError):
        return None  # Can't parse — proceed normally

    if toxicity.get("is_toxic", False):
        return types.Content(
            role="model",
            parts=[types.Part(text='{"pipeline_action": "TERMINATE", "reason": "Skipped — toxic review"}')],
        )

    return None  # Not toxic — proceed normally


def write_human_review_after_guardrail(callback_context):
    """Write failed responses to human review queue file.

    Used as after_agent_callback on the guardrail agent (stage 6).
    If guardrail_action is REVISE or ESCALATE_TO_HUMAN, appends to file.
    """
    state = callback_context.state
    guardrail_raw = state.get("guardrail_result", "{}")

    try:
        guardrail = json.loads(guardrail_raw) if isinstance(guardrail_raw, str) else guardrail_raw
    except (json.JSONDecodeError, TypeError):
        return None

    action = guardrail.get("guardrail_action", "PUBLISH")
    if action in ("REVISE", "ESCALATE_TO_HUMAN"):
        entry = {
            "review_input": state.get("review_input", "{}"),
            "response_result": state.get("response_result", "{}"),
            "guardrail_result": guardrail_raw,
            "guardrail_action": action,
            "violations": guardrail.get("violations", []),
            "queued_at": datetime.utcnow().isoformat(),
        }

        os.makedirs(os.path.dirname(HUMAN_REVIEW_FILE), exist_ok=True)
        with open(HUMAN_REVIEW_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

        print(f"  ⚠ Response queued for human review ({action})")

    return None  # Don't override the guardrail's output
