#!/usr/bin/env python3
"""
Automated smoke test for T2 Managed RAG readiness validation.
"""

import sys

from rag_client import create_rag_client


def run_smoke_test() -> bool:
    print("Initializing Governed RAG Client for readiness verification...")
    client = create_rag_client()

    print("Executing semantic retrieval against known smoke document...")
    query = "What is the IDP verification code for Managed RAG?"
    result = client.retrieve(query, top_k=1)

    if result.get("status") == "success" and result.get("results"):
        top_match = result["results"][0]
        content = top_match.get("content", "")
        if "IDP-RAG-VERIFIED-2026" in content:
            print(f"Readiness verified successfully! Matched content: {content}")
            return True

    print(f"RAG Smoke test verification failed! Result: {result}", file=sys.stderr)
    return False


if __name__ == "__main__":
    success = run_smoke_test()
    if not success:
        sys.exit(1)
    sys.exit(0)
