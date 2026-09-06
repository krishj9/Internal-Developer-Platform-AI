#!/usr/bin/env python3
"""
CLI Query Client for the Math Reasoning Agent.

Usage:
    uv run python query.py "Add 200 to 423 and subtract 98 from it"
"""

import argparse
import json
import os
import sys

try:
    from math_agent import create_agent
except ImportError:
    from .math_agent import create_agent


def print_formatted_result(result: dict):
    print("\n" + "=" * 60)
    print("🤖 MATH REASONING AGENT EXECUTION")
    print("=" * 60)
    print(f"Prompt:       \"{result.get('prompt', '')}\"")
    print(f"Status:       {result.get('status', '').upper()}")
    print(f"Model:        {result.get('model', 'gemini-2.5-flash')}")
    print("-" * 60)

    tool_calls = result.get("tool_calls", [])
    if tool_calls:
        print("🛠️  AUTONOMOUS TOOL INVOCATION SEQUENCE:")
        for idx, tc in enumerate(tool_calls, start=1):
            tool = tc.get("tool", "")
            args = tc.get("args", {})
            out = tc.get("output", tc.get("error", ""))
            print(f"   [{idx}] {tool}({args}) => {out}")
        print("-" * 60)

    if result.get("status") == "success":
        print(f"🎯 Numerical Result: {result.get('result_value')}")
        print(f"📝 Reasoning Answer: {result.get('final_answer') or result.get('response', '')}")
    else:
        print(f"❌ Error Message:    {result.get('message') or result.get('error', '')}")

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Query the Math Reasoning Agent.")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Add 200 to 423 and subtract 98 from it",
        help="Natural language math prompt to solve",
    )
    parser.add_argument("--config", "-c", default="idp-config.json", help="Path to idp-config.json")
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Query live deployed Vertex AI Reasoning Engine",
    )
    args = parser.parse_args()

    # Cloud query mode
    if args.cloud and os.path.exists("deployed-agent.json"):
        with open("deployed-agent.json") as f:
            status_data = json.load(f)
        resource_name = status_data.get("resource_name")
        print(f"Querying live Vertex AI Reasoning Engine: {resource_name}...")
        try:
            import vertexai
            from vertexai.preview import reasoning_engines

            vertexai.init(
                project=status_data.get("project_id"),
                location=status_data.get("region"),
            )
            engine = reasoning_engines.ReasoningEngine(resource_name)
            res = engine.query(prompt=args.prompt)
            result_payload = (
                res if isinstance(res, dict) else {"status": "success", "response": str(res)}
            )
            print_formatted_result(result_payload)
            return
        except Exception as e:
            print(
                f"Live cloud query failed: {e}. Falling back to local agent execution...",
                file=sys.stderr,
            )

    # Local / Deterministic Agent Mode
    agent = create_agent(args.config)
    res = agent.query(args.prompt)
    print_formatted_result(res)


if __name__ == "__main__":
    main()
