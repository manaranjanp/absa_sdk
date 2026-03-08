"""
ABSA Pipeline Orchestrator
----------------------------
Creates the SequentialAgent pipeline that orchestrates all 6 subagents.
Supports any LLM provider via LiteLLM (OpenAI, Anthropic, Google, Grok, etc.).
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Optional

from google.adk.agents import SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from agents import (
    create_toxicity_agent,
    create_aspect_extraction_agent,
    create_sentiment_analysis_agent,
    create_policy_escalation_agent,
    create_response_generation_agent,
    create_output_guardrail_agent,
)
from pipeline.callbacks import (
    check_toxicity_before_agent,
    write_human_review_after_guardrail,
)


# Path to the pipeline results log file
RESULTS_LOG_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "pipeline_results.log"
)

# Stage names for console logging
STAGE_NAMES = [
    "Toxicity Detection",
    "Aspect Extraction",
    "Sentiment Analysis",
    "Policy Evaluation & Escalation",
    "Response Generation",
    "Output Guardrail",
]


def create_absa_pipeline(model_name: str = "openai/gpt-4o") -> SequentialAgent:
    """Create the full ABSA SequentialAgent pipeline.

    Args:
        model_name: LiteLLM model string (e.g., "openai/gpt-4o",
                    "anthropic/claude-3-5-sonnet-20241022", "groq/llama3-8b-8192").

    Returns:
        A SequentialAgent that processes reviews through all 6 stages.
    """
    model = LiteLlm(model=model_name)

    # Stage 1: Toxicity — runs first, no before_callback needed
    toxicity = create_toxicity_agent(model)

    # Stages 2-5: Skip if toxic
    aspect = create_aspect_extraction_agent(model)
    aspect.before_agent_callback = check_toxicity_before_agent

    sentiment = create_sentiment_analysis_agent(model)
    sentiment.before_agent_callback = check_toxicity_before_agent

    escalation = create_policy_escalation_agent(model)
    escalation.before_agent_callback = check_toxicity_before_agent

    response = create_response_generation_agent(model)
    response.before_agent_callback = check_toxicity_before_agent

    # Stage 6: Guardrail — skip if toxic + write to human review if failed
    guardrail = create_output_guardrail_agent(model)
    guardrail.before_agent_callback = check_toxicity_before_agent
    guardrail.after_agent_callback = write_human_review_after_guardrail

    pipeline = SequentialAgent(
        name="absa_pipeline",
        description="ABSA Review Processing Pipeline — 6-stage with conditional flow",
        sub_agents=[toxicity, aspect, sentiment, escalation, response, guardrail],
    )

    return pipeline


async def run_pipeline(
    review: dict,
    model_name: str = "openai/gpt-4o",
    pipeline: Optional[SequentialAgent] = None,
    session_service: Optional[InMemorySessionService] = None,
    runner: Optional[Runner] = None,
) -> dict:
    """Execute the ABSA pipeline for a single review.

    Args:
        review: Review dict with review_id and review_text.
        model_name: LiteLLM model string for the pipeline.
        pipeline: Optional pre-created pipeline (reuse across reviews).
        session_service: Optional pre-created session service.
        runner: Optional pre-created runner.

    Returns:
        Dict with pipeline results from all stages.
    """
    # Create pipeline if not provided
    if pipeline is None:
        pipeline = create_absa_pipeline(model_name)

    # Create session service and runner if not provided
    if session_service is None:
        session_service = InMemorySessionService()

    if runner is None:
        runner = Runner(
            agent=pipeline,
            app_name="absa_pipeline_app",
            session_service=session_service,
        )

    # Create a new session for this review
    review_id = review.get("review_id", "unknown")
    session = await session_service.create_session(
        app_name="absa_pipeline_app",
        user_id="pipeline_user",
        state={"review_input": json.dumps(review)},
    )

    print(f"\n{'='*60}")
    print(f"  Processing Review: {review_id}")
    print(f"{'='*60}")

    # Run the pipeline
    user_message = types.Content(
        role="user",
        parts=[
            types.Part(text=f"Process this review:\n{json.dumps(review, indent=2)}")
        ],
    )

    results = {}
    current_stage = 0

    async for event in runner.run_async(
        user_id="pipeline_user",
        session_id=session.id,
        new_message=user_message,
    ):
        # Track agent transitions for logging
        if hasattr(event, "author") and event.author:
            agent_name = event.author
            stage_idx = _get_stage_index(agent_name)
            if stage_idx is not None and stage_idx != current_stage:
                current_stage = stage_idx
                print(f"\n  [{current_stage + 1}/6] {STAGE_NAMES[current_stage]}...")

        # Capture final text outputs
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    author = getattr(event, "author", "unknown")
                    results[author] = part.text

    # Extract structured results from session state
    final_session = await session_service.get_session(
        app_name="absa_pipeline_app",
        user_id="pipeline_user",
        session_id=session.id,
    )

    state = final_session.state if final_session else {}

    pipeline_output = {
        "review_id": review_id,
        "review_text": review.get("review_text", ""),
        "toxicity_result": _safe_parse(state.get("toxicity_result", "{}")),
        "aspect_result": _safe_parse(state.get("aspect_result", "{}")),
        "sentiment_result": _safe_parse(state.get("sentiment_result", "{}")),
        "escalation_result": _safe_parse(state.get("escalation_result", "{}")),
        "response_result": _safe_parse(state.get("response_result", "{}")),
        "guardrail_result": _safe_parse(state.get("guardrail_result", "{}")),
    }

    # Print summary
    _print_summary(pipeline_output)

    return pipeline_output


def _get_stage_index(agent_name: str) -> Optional[int]:
    """Map agent name to pipeline stage index."""
    mapping = {
        "toxicity_detection_agent": 0,
        "aspect_extraction_agent": 1,
        "sentiment_analysis_agent": 2,
        "policy_escalation_agent": 3,
        "response_generation_agent": 4,
        "output_guardrail_agent": 5,
    }
    return mapping.get(agent_name)


def _safe_parse(text: str):
    """Safely parse JSON from agent output, returning raw text on failure."""
    if not text:
        return {}
    try:
        # Handle cases where output might have markdown code fences
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return {"raw_output": text}


def _print_summary(output: dict):
    """Print a concise pipeline execution summary and write it to the results log."""
    lines = []
    lines.append(f"  Review ID:   {output['review_id']}")
    lines.append(f"  Timestamp:   {datetime.utcnow().isoformat()}")
    lines.append(f"  Review:      {output.get('review_text', '')}")

    # Toxicity
    tox = output.get("toxicity_result", {})
    is_toxic = tox.get("is_toxic", False)
    tox_score = tox.get("toxicity_score", "N/A")
    status = "TOXIC — Pipeline terminated" if is_toxic else "Clean"
    lines.append(f"  Toxicity:    {status} (score: {tox_score})")

    if not is_toxic:
        # Aspects
        aspects = output.get("aspect_result", {})
        aspect_list = aspects.get("aspects", [])
        codes = [a.get("aspect_code", "?") for a in aspect_list]
        lines.append(f"  Aspects:     {', '.join(codes) if codes else 'None extracted'}")

        # Sentiments
        sents = output.get("sentiment_result", {})
        overall = sents.get("overall_sentiment", "N/A")
        overall_score = sents.get("overall_sentiment_score", "N/A")
        lines.append(f"  Overall:     {overall} (score: {overall_score})")

        # Escalation
        esc = output.get("escalation_result", {})
        ticket = esc.get("escalation_ticket")
        if ticket:
            lines.append(f"  Escalation:  {ticket.get('priority', '?')} priority, {ticket.get('sla_hours', '?')}h SLA")
        else:
            lines.append(f"  Escalation:  No ticket created")

        # Guardrail
        guard = output.get("guardrail_result", {})
        passed = guard.get("guardrail_passed", "N/A")
        g_action = guard.get("guardrail_action", "N/A")
        lines.append(f"  Guardrail:   {'PASSED' if passed else 'FAILED'} → {g_action}")

        # Response — full text, not truncated
        resp = output.get("response_result", {})
        response_text = resp.get("response_text", "")
        if response_text:
            lines.append(f"  Response:    {response_text}")

    # Print to console
    separator = f"{'─'*60}"
    print(f"\n{separator}")
    for line in lines:
        print(line)
    print(f"{separator}\n")

    # Write to file
    os.makedirs(os.path.dirname(RESULTS_LOG_FILE), exist_ok=True)
    with open(RESULTS_LOG_FILE, "a") as f:
        f.write(separator + "\n")
        for line in lines:
            f.write(line + "\n")
        f.write(separator + "\n\n")
