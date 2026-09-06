#!/usr/bin/env python3
"""
Deploy the Math Reasoning Agent to Google Cloud Vertex AI Agent Engine.

This script reads the workload configuration file (`idp-config.json`) exported from the IDP,
packages the agent code and arithmetic tools, and publishes the Reasoning Engine instance.
"""

import argparse
import json
import os
import sys

try:
    from math_agent import MathReasoningAgent
except ImportError:
    from .math_agent import MathReasoningAgent


def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.", file=sys.stderr)
        print("Obtain it from the IDP Portal or run:", file=sys.stderr)
        print("  idp deployments config <deployment_id> --out idp-config.json", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        return json.load(f)


def deploy_to_vertex_ai(config: dict, dry_run: bool = False):
    dep_id = config.get("deployment_id", "unknown")
    project_id = config.get("project_id") or os.getenv("GCP_PROJECT", "mybrightday-dev")
    region = config.get("region", "us-central1")
    staging_bucket = config.get("staging_bucket") or f"idp-state-{project_id}"
    runtime_sa = config.get("runtime_service_account")
    model_name = config.get("model_name", "gemini-2.5-flash")

    print("=== Deploying Math Agent to Vertex AI Agent Engine ===")
    print(f"  • IDP Deployment ID:       {dep_id}")
    print(f"  • GCP Project:             {project_id}")
    print(f"  • Region:                  {region}")
    print(f"  • Foundation Model:        {model_name}")
    print(f"  • Runtime Service Account: {runtime_sa}")
    print(f"  • Staging Bucket:          {staging_bucket}")
    print("=====================================================")

    if dry_run:
        print("\n[DRY RUN]: Validation succeeded! Packaging simulation complete.")
        simulated_resource = (
            f"projects/{project_id}/locations/{region}/reasoningEngines/re-sim-{dep_id[:8]}"
        )
        print(f"Simulated Reasoning Engine Resource: {simulated_resource}")
        return simulated_resource

    try:
        import vertexai
        from vertexai.preview import reasoning_engines

        bucket_uri = (
            f"gs://{staging_bucket}"
            if not staging_bucket.startswith("gs://")
            else staging_bucket
        )
        vertexai.init(
            project=project_id,
            location=region,
            staging_bucket=bucket_uri,
        )

        agent_instance = MathReasoningAgent(
            model_name=model_name,
            project_id=project_id,
            location=region,
        )

        print("Packaging agent and publishing to Vertex AI Reasoning Engine...")
        remote_engine = reasoning_engines.ReasoningEngine.create(
            reasoning_engine=agent_instance,
            requirements=[
                "google-cloud-aiplatform>=1.70.0",
                "google-genai>=0.1.0",
                "pydantic>=2.10.0",
            ],
            display_name=f"math-agent-{dep_id}",
            description=f"Governed Math Tool Agent on IDP T1 deployment {dep_id}",
        )

        resource_name = remote_engine.resource_name
        print("\nSuccessfully deployed to Vertex AI Agent Engine!")
        print(f"Resource Name: {resource_name}")

        # Save deployment output for query client
        status_file = "deployed-agent.json"
        with open(status_file, "w") as f:
            json.dump({
                "deployment_id": dep_id,
                "resource_name": resource_name,
                "project_id": project_id,
                "region": region,
                "model_name": model_name,
            }, f, indent=2)
        print(f"Saved deployment reference to '{status_file}'.")
        return resource_name

    except ImportError:
        print(
            "Error: 'google-cloud-aiplatform' is required to deploy to Vertex AI.",
            file=sys.stderr,
        )
        print("Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Deployment failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Math Reasoning Agent to Vertex AI Agent Engine."
    )
    parser.add_argument("--config", "-c", default="idp-config.json", help="Path to idp-config.json")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate deployment packaging without cloud API calls",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    deploy_to_vertex_ai(config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
