"""
IDP CLI Client for Governed Agentic AI on GCP.
"""

import json
import sys
import uuid
from pathlib import Path
from typing import Any

import click
import httpx

SESSION_PATH = Path.home() / ".idp" / "session.json"


def save_session(data: dict[str, Any]) -> None:
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_PATH, "w") as f:
        json.dump(data, f)


def load_session() -> dict[str, Any]:
    if not SESSION_PATH.exists():
        click.echo("Error: Not logged in. Run 'idp login' first.", err=True)
        sys.exit(1)
    with open(SESSION_PATH) as f:
        return json.load(f)


def get_client() -> tuple[httpx.Client, str]:
    session = load_session()
    base_url = session.get("base_url", "http://127.0.0.1:8000")
    token = session.get("token")
    client = httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=15.0,
    )
    return client, base_url


@click.group()
def cli():
    """IDP CLI - Governed Agentic AI Infrastructure Control Plane."""
    pass


@cli.command("login")
@click.option("--username", "-u", prompt=True, help="IDP Username")
@click.option("--password", "-p", prompt=True, hide_input=True, help="IDP Password")
@click.option("--url", default="http://127.0.0.1:8000", help="IDP API Base URL")
def login(username, password, url):
    """Authenticate and store session token."""
    try:
        with httpx.Client(base_url=url, timeout=10.0) as client:
            res = client.post("/auth/login", json={"username": username, "password": password})
            if res.status_code != 200:
                click.echo(f"Login failed: {res.text}", err=True)
                sys.exit(1)
            data = res.json()
            token = data["access_token"]
            save_session({"token": token, "base_url": url, "username": username})
            click.echo(f"Successfully authenticated as '{username}'.")
    except Exception as e:
        click.echo(f"Connection error: {e}", err=True)
        sys.exit(1)


@cli.group("templates")
def templates_group():
    """Manage and inspect governed templates."""
    pass


@templates_group.command("list")
def list_templates():
    """List available governed AI templates."""
    client, _ = get_client()
    res = client.get("/templates")
    if res.status_code != 200:
        click.echo(f"Error: {res.text}", err=True)
        sys.exit(1)
    templates = res.json()
    click.echo(f"{'TEMPLATE ID':<24} {'VERSION':<10} {'COST TIER':<12} {'NAME'}")
    click.echo("-" * 70)
    for t in templates:
        tier = t.get("cost_tier", "low")
        click.echo(
            f"{t['template_id']:<24} {t['template_version']:<10} {tier:<12} {t['display_name']}"
        )


@cli.group("requests")
def requests_group():
    """Submit and monitor lifecycle requests."""
    pass


@requests_group.command("create")
@click.option("--template", "-t", required=True, help="Template ID")
@click.option("--version", "-v", default="2.0.0", help="Template Version")
@click.option("--workspace", "-w", default="ws-dev", help="Target Workspace")
@click.option("--environment", "-e", default="dev", help="Target Environment (dev/prod)")
@click.option("--inputs-json", "-i", default="{}", help="JSON string of template inputs")
def create_request(template, version, workspace, environment, inputs_json):
    """Submit asynchronous provisioning request."""
    client, _ = get_client()
    try:
        parsed_inputs = json.loads(inputs_json)
    except Exception as e:
        click.echo(f"Invalid JSON inputs: {e}", err=True)
        sys.exit(1)

    payload = {
        "workspace": workspace,
        "template_id": template,
        "template_version": version,
        "environment": environment,
        "inputs": parsed_inputs,
    }
    idemp_key = f"cli-req-{uuid.uuid4().hex[:8]}"
    res = client.post("/requests", json=payload, headers={"Idempotency-Key": idemp_key})
    if res.status_code != 202:
        click.echo(f"Request failed ({res.status_code}): {res.text}", err=True)
        sys.exit(1)
    data = res.json()
    click.echo("Request dispatched successfully!")
    click.echo(f"Request ID:    {data['request_id']}")
    click.echo(f"Deployment ID: {data['deployment_id']}")
    click.echo(f"Status:        {data['status']}")


@requests_group.command("status")
@click.argument("request_id")
def request_status(request_id):
    """Get status and telemetry for a request."""
    client, _ = get_client()
    res = client.get(f"/requests/{request_id}")
    if res.status_code != 200:
        click.echo(f"Error: {res.text}", err=True)
        sys.exit(1)
    data = res.json()
    click.echo(f"Request ID:    {data['request_id']}")
    click.echo(f"Deployment ID: {data['deployment_id']}")
    click.echo(f"Status:        {data['status']}")
    click.echo(f"Summary:       {data.get('safe_summary', 'N/A')}")


@cli.group("deployments")
def deployments_group():
    """List and manage active deployments."""
    pass


@deployments_group.command("list")
@click.option("--workspace", "-w", default=None, help="Filter by workspace")
def list_deployments(workspace):
    """List deployments."""
    client, _ = get_client()
    url = f"/deployments?workspace={workspace}" if workspace else "/deployments"
    res = client.get(url)
    if res.status_code != 200:
        click.echo(f"Error: {res.text}", err=True)
        sys.exit(1)
    deps = res.json()
    click.echo(f"{'DEPLOYMENT ID':<22} {'TEMPLATE':<20} {'ENV':<8} {'STATUS':<14} {'EXPIRES'}")
    click.echo("-" * 75)
    for d in deps:
        exp = d.get("expires_at", "Never")[:10] if d.get("expires_at") else "Never"
        click.echo(
            f"{d['deployment_id']:<22} {d['template_id']:<20} {d['environment']:<8} "
            f"{d['status']:<14} {exp}"
        )


@deployments_group.command("config")
@click.argument("deployment_id")
@click.option("--out", "-o", default=None, help="Output file path (e.g. idp-config.json)")
def get_deployment_config(deployment_id, out):
    """Retrieve or export workload configuration for a deployment."""
    client, _ = get_client()
    res = client.get(f"/deployments/{deployment_id}/config")
    if res.status_code != 200:
        click.echo(f"Error: {res.text}", err=True)
        sys.exit(1)
    data = res.json()
    safe_config = data.get("safe_config", {})
    outputs = safe_config.get("outputs", {})
    workload_config = {
        "deployment_id": safe_config.get("deployment_id"),
        "workspace": safe_config.get("workspace"),
        "environment": safe_config.get("environment"),
        "project_id": safe_config.get("project_id"),
        "template_id": safe_config.get("template_id"),
        "template_version": safe_config.get("template_version"),
        "status": safe_config.get("status"),
        "model_name": outputs.get("model_name"),
        "region": outputs.get("region"),
        "runtime_service_account": outputs.get("runtime_sa_email"),
        "staging_bucket": (
            outputs.get("staging_bucket") or f"idp-state-{safe_config.get('project_id')}"
        ),
        "tool_secret_id": outputs.get("tool_secret_id"),
        "alert_policy_id": outputs.get("alert_policy_id"),
        "agent_engine_resource_id": outputs.get("agent_engine_resource_id"),
        "raw_outputs": outputs,
    }
    config_json = json.dumps(workload_config, indent=2)
    if out:
        with open(out, "w") as f:
            f.write(config_json + "\n")
        click.echo(f"Workload configuration exported to: {out}")
    else:
        click.echo(config_json)


@deployments_group.command("destroy")
@click.argument("deployment_id")
def destroy_deployment(deployment_id):
    """Submit destroy request for a deployment."""
    client, _ = get_client()
    idemp_key = f"cli-destroy-{uuid.uuid4().hex[:8]}"
    res = client.post(
        f"/deployments/{deployment_id}/destroy",
        headers={"Idempotency-Key": idemp_key},
    )
    if res.status_code != 202:
        click.echo(f"Error: {res.text}", err=True)
        sys.exit(1)
    data = res.json()
    click.echo("Destroy request dispatched!")
    click.echo(f"Request ID: {data['request_id']}")


@cli.group("agent")
def agent_group():
    """Interact with deployed agent reasoning engines."""
    pass


@agent_group.command("query")
@click.argument("deployment_id")
@click.argument("prompt")
def query_agent(deployment_id, prompt):
    """Send a prompt to a deployed agent."""
    client, _ = get_client()
    res = client.post(f"/deployments/{deployment_id}/query", json={"prompt": prompt})
    if res.status_code != 200:
        click.echo(f"Error: {res.text}", err=True)
        sys.exit(1)
    data = res.json()
    click.echo(f"Deployment: {data['deployment_id']}")
    click.echo(f"Model:      {data.get('model', 'N/A')}")
    click.echo(f"Guardrails: {data.get('guardrail_status', 'PASSED')}")
    tools = data.get("tools_executed", [])
    if tools:
        click.echo("\nExecuted Tools:")
        for t in tools:
            tool_name = t.get("tool")
            args = t.get("args")
            out = t.get("output")
            click.echo(f"  • {tool_name}({args}) -> {out}")
    click.echo(f"\nResponse:\n{data['response']}")


@agent_group.command("ping")
@click.argument("deployment_id")
def ping_agent(deployment_id):
    """Health check a deployed agent."""
    client, _ = get_client()
    res = client.post(f"/deployments/{deployment_id}/query", json={"prompt": "ping"})
    if res.status_code != 200:
        click.echo(f"Health check failed: {res.text}", err=True)
        sys.exit(1)
    data = res.json()
    if data.get("response") == "pong":
        click.echo(f"Agent {deployment_id} is HEALTHY and READY (pong received).")
    else:
        click.echo(f"Response: {data.get('response')}")


@cli.group("governance")
def governance_group():
    """Governance and Model Armor inspection."""
    pass


@governance_group.command("inspect")
@click.argument("text")
@click.option("--point", default="prompt", help="Inspection point (prompt/tool_input/model_output)")
@click.option("--mode", default="block", help="Mode (block/redact/allow_with_audit)")
def inspect_text(text, point, mode):
    """Inspect text against Model Armor guardrails."""
    client, _ = get_client()
    res = client.post("/governance/inspect", json={"text": text, "point": point, "mode": mode})
    if res.status_code != 200:
        click.echo(f"Error: {res.text}", err=True)
        sys.exit(1)
    data = res.json()
    click.echo(f"Passed:       {data['passed']}")
    click.echo(f"Action Taken: {data['action_taken']}")
    if data.get("violations"):
        click.echo(f"Violations:   {data['violations']}")
    if data.get("processed_text"):
        click.echo(f"Processed:    {data['processed_text']}")


if __name__ == "__main__":
    cli()
