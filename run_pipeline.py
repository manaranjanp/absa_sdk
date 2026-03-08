#!/usr/bin/env python3
"""
ABSA Pipeline Runner
---------------------
CLI script to run the ABSA agent pipeline for one or more customer reviews.

Usage:
    # Run with a single review (JSON string)
    python run_pipeline.py --review '{"review_id":"test1", ...}'

    # Run a batch from the sample dataset
    python run_pipeline.py --batch data/sample_reviews.json

    # Run N random samples from the dataset
    python run_pipeline.py --sample 3

    # Specify a different LLM provider
    python run_pipeline.py --sample 3 --model anthropic/claude-3-5-sonnet-20241022

    # Enable verbose LiteLLM logging
    python run_pipeline.py --sample 1 --verbose
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from observability import setup_observability, setup_litellm_logging
from pipeline.absa_pipeline import create_absa_pipeline, run_pipeline
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner


def load_sample_reviews(path: str = "data/sample_reviews.json") -> list:
    """Load reviews from the sample dataset file."""
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    with open(full_path, "r") as f:
        return json.load(f)


async def run_single_review(review: dict, model_name: str):
    """Process a single review through the pipeline."""
    print(f"\n[Pipeline] Model: {model_name}")
    print(f"[Pipeline] Starting single review processing...")

    start = time.time()
    result = await run_pipeline(review, model_name=model_name)
    elapsed = time.time() - start

    print(f"[Pipeline] Completed in {elapsed:.1f}s")
    return result


async def run_batch(reviews: list, model_name: str):
    """Process a batch of reviews sequentially through the pipeline."""
    print(f"\n[Pipeline] Model: {model_name}")
    print(f"[Pipeline] Processing batch of {len(reviews)} reviews...")

    # Initialize shared resources
    pipeline = create_absa_pipeline(model_name)
    session_service = InMemorySessionService()
    runner = Runner(
        agent=pipeline,
        app_name="absa_pipeline_app",
        session_service=session_service,
    )

    results = []
    total_start = time.time()

    for i, review in enumerate(reviews):
        print(f"\n{'#'*60}")
        print(f"  Review {i + 1} of {len(reviews)}")
        print(f"{'#'*60}")

        start = time.time()
        result = await run_pipeline(
            review,
            model_name=model_name,
            pipeline=pipeline,
            session_service=session_service,
            runner=runner,
        )
        elapsed = time.time() - start
        print(f"[Pipeline] Review {i + 1} completed in {elapsed:.1f}s")
        results.append(result)

    total_elapsed = time.time() - total_start

    # Print batch summary
    print(f"\n{'='*60}")
    print(f"  BATCH SUMMARY")
    print(f"{'='*60}")
    print(f"  Total reviews:   {len(reviews)}")
    print(f"  Total time:      {total_elapsed:.1f}s")
    print(f"  Avg per review:  {total_elapsed / len(reviews):.1f}s")

    toxic_count = sum(1 for r in results if r.get("toxicity_result", {}).get("is_toxic", False))
    print(f"  Toxic (terminated): {toxic_count}")
    print(f"  Processed:       {len(reviews) - toxic_count}")

    escalated = sum(1 for r in results if r.get("escalation_result", {}).get("escalation_ticket"))
    print(f"  Escalations:     {escalated}")

    passed = sum(1 for r in results
                 if r.get("guardrail_result", {}).get("guardrail_passed", False))
    print(f"  Guardrail passed: {passed}")
    print(f"{'='*60}\n")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="ABSA Agent Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--review",
        type=str,
        help="Single review as a JSON string",
    )
    group.add_argument(
        "--batch",
        type=str,
        help="Path to JSON file with array of reviews",
    )
    group.add_argument(
        "--sample",
        type=int,
        help="Run N random samples from the default dataset",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("DEFAULT_MODEL", "openai/gpt-4o"),
        help="LiteLLM model string (default: openai/gpt-4o)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose LiteLLM logging",
    )

    args = parser.parse_args()

    # Setup observability and logging
    setup_observability()
    setup_litellm_logging(verbose=args.verbose)

    print(f"\n[ABSA Pipeline] Starting...")
    print(f"[ABSA Pipeline] Model: {args.model}")

    if args.review:
        review = json.loads(args.review)
        asyncio.run(run_single_review(review, args.model))

    elif args.batch:
        with open(args.batch, "r") as f:
            reviews = json.load(f)
        asyncio.run(run_batch(reviews, args.model))

    elif args.sample:
        all_reviews = load_sample_reviews()
        n = min(args.sample, len(all_reviews))
        selected = random.sample(all_reviews, n)
        print(f"[ABSA Pipeline] Selected {n} random reviews from dataset")
        asyncio.run(run_batch(selected, args.model))


if __name__ == "__main__":
    main()
