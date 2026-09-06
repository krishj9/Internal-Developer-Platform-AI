#!/usr/bin/env python3
"""
Automated smoke test for T1 Agent Engine readiness validation.
"""

import sys

from agent import create_agent


def run_smoke_test() -> bool:
    print("Initializing Agent instance for smoke test...")
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
