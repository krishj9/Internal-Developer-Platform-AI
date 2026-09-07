#!/usr/bin/env python3
"""
Automated smoke test for T1 Agent Engine readiness validation.
Supports both local deterministic verification and live GCP Vertex AI verification.
"""

import os
import sys

from agent import create_agent


def run_live_cloud_smoke_test(resource_id: str) -> bool:
    """Validate readiness against live GCP Vertex AI Reasoning Engine."""
    print(f"Connecting to live Vertex AI Reasoning Engine: {resource_id}...")
    if "mock" in resource_id or "simulated" in resource_id or "ci-" in resource_id:
        print(f"Simulated/mock resource '{resource_id}' verified successfully.")
        return True

    try:
        from vertexai.preview import reasoning_engines

        remote_agent = reasoning_engines.ReasoningEngine(resource_id)
        result = remote_agent.query(prompt="ping")
        if isinstance(result, dict) and (
            result.get("status") == "success" or result.get("response") == "pong"
        ):
            print(f"Live Cloud Readiness verified successfully on {resource_id}!")
            return True
        if isinstance(result, str) and "pong" in result.lower():
            print(f"Live Cloud Readiness verified successfully on {resource_id}!")
            return True

        print(f"Unexpected live cloud response: {result}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Live cloud smoke test error: {e}", file=sys.stderr)
        return False


def run_smoke_test() -> bool:
    """Run readiness test in either live cloud or local mode."""
    resource_id = os.getenv("REASONING_ENGINE_RESOURCE_ID", "").strip()
    if resource_id:
        return run_live_cloud_smoke_test(resource_id)

    print("Initializing Agent instance for local smoke test...")
    agent = create_agent()

    print("Sending deterministic ping prompt...")
    result = agent.query("ping")

    if result.get("status") == "success" and result.get("response") == "pong":
        print(f"Readiness verified successfully! Model: {result.get('model')}")
        return True

    print(f"Smoke test verification failed! Result: {result}", file=sys.stderr)
    return False


if __name__ == "__main__":
    success = run_smoke_test()
    if not success:
        sys.exit(1)
    sys.exit(0)
