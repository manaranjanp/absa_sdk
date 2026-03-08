"""
LangSmith Observability Configuration
--------------------------------------
Configures LiteLLM callbacks to send all LLM interaction traces
to LangSmith for monitoring, debugging, and evaluation.
"""

import os
import litellm
from dotenv import load_dotenv

load_dotenv()


def setup_observability():
    """Initialize LangSmith tracing via LiteLLM callbacks.

    Requires LANGSMITH_API_KEY in environment. If not set,
    observability is silently disabled.
    """
    langsmith_key = os.getenv("LANGSMITH_API_KEY", "")

    if langsmith_key and langsmith_key != "your-langsmith-api-key-here":
        litellm.callbacks = ["langsmith"]
        litellm.langsmith_batch_size = 5  # Use 1 for local testing

        project = os.getenv("LANGSMITH_PROJECT", "absa-agent-pipeline")
        os.environ["LANGSMITH_PROJECT"] = project

        print(f"[Observability] LangSmith tracing enabled → project: {project}")
    else:
        print("[Observability] LangSmith not configured — tracing disabled")


def setup_litellm_logging(verbose: bool = False):
    """Configure LiteLLM logging level.

    Args:
        verbose: If True, enable detailed LiteLLM debug logs.
    """
    if verbose:
        litellm.set_verbose = True
    else:
        # Suppress noisy litellm logs in normal operation
        import logging
        logging.getLogger("LiteLLM").setLevel(logging.WARNING)
