"""
Unit tests for T1 Agent Engine template and agent.
"""

import importlib.util
import sys
from pathlib import Path

import yaml


def _load_t1_module(module_name: str, rel_path: str):
    file_path = Path(__file__).parent.parent / rel_path
    dir_path = str(file_path.parent)
    if dir_path not in sys.path:
        sys.path.insert(0, dir_path)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


t1_agent = _load_t1_module("t1_agent_mod", "agent/agent.py")
t1_smoke = _load_t1_module("t1_smoke_mod", "agent/smoke_test.py")


def test_t1_template_manifest_schema():
    """Verify template.yaml conforms to governed template schema."""
    manifest_path = Path(__file__).parent.parent / "template.yaml"
    assert manifest_path.exists(), "template.yaml must exist"

    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["id"] == "t1-agent-engine"
    assert data["version"] == "2.0.0"
    assert "dev" in data["supported_environments"]
    assert data["cost_tier"] == "low"
    assert data["inputs"]["type"] == "object"
    assert data["inputs"]["additionalProperties"] is False

    # Check input constraints
    props = data["inputs"]["properties"]
    assert "agent_name" in props
    assert "model_name" in props
    assert "region" in props

    # Check allowed outputs
    allowed_outputs = data["output_contract"]["allowed_outputs"]
    assert "deployment_id" in allowed_outputs
    assert "agent_name" in allowed_outputs
    assert "model_name" in allowed_outputs


def test_t1_agent_query_ping():
    """Verify GovernedAgent ping response."""
    agent = t1_agent.GovernedAgent(model_name="gemini-2.5-flash")
    res = agent.query("ping")
    assert res["status"] == "success"
    assert res["response"] == "pong"


def test_t1_agent_query_empty():
    """Verify GovernedAgent handles empty prompt safely."""
    agent = t1_agent.create_agent()
    res = agent.query("")
    assert res["status"] == "error"
    assert "Prompt cannot be empty" in res["message"]


def test_t1_smoke_test_function():
    """Verify automated smoke test script returns True."""
    assert t1_smoke.run_smoke_test() is True
