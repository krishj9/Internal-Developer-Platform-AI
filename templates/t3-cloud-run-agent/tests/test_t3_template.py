"""
Unit and integration tests for T3 Cloud Run Agent template and service.
"""

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml
from httpx import ASGITransport, AsyncClient


def _load_t3_module(module_name: str, rel_path: str):
    file_path = Path(__file__).parent.parent / rel_path
    dir_path = str(file_path.parent)
    if dir_path not in sys.path:
        sys.path.insert(0, dir_path)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


t3_agent = _load_t3_module("t3_agent_unique", "service/agent.py")
sys.modules["agent"] = t3_agent
t3_main = _load_t3_module("t3_main_unique", "service/main.py")
t3_smoke = _load_t3_module("t3_smoke_unique", "service/smoke_test.py")


def test_t3_template_manifest_schema():
    """Verify template.yaml conforms to governed template schema."""
    manifest_path = Path(__file__).parent.parent / "template.yaml"
    assert manifest_path.exists(), "template.yaml must exist"

    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["id"] == "t3-cloud-run-agent"
    assert data["version"] == "2.0.0"
    assert "dev" in data["supported_environments"]
    assert data["cost_tier"] == "medium"
    assert data["inputs"]["type"] == "object"
    assert data["inputs"]["additionalProperties"] is False

    # Check input constraints
    props = data["inputs"]["properties"]
    assert "service_name" in props
    assert "model_name" in props
    assert "cpu" in props
    assert "memory" in props
    assert "max_instances" in props

    # Check allowed outputs
    allowed_outputs = data["output_contract"]["allowed_outputs"]
    assert "deployment_id" in allowed_outputs
    assert "service_name" in allowed_outputs
    assert "service_url" in allowed_outputs
    assert "runtime_sa_email" in allowed_outputs


def test_t3_agent_query_ping():
    """Verify GovernedAgent ping response."""
    agent = t3_agent.GovernedAgent(model_name="gemini-2.5-flash")
    res = agent.query("ping")
    assert res["status"] == "success"
    assert res["response"] == "pong"
    assert res["runtime"] == "cloud-run"


def test_t3_agent_query_empty():
    """Verify GovernedAgent handles empty prompt safely."""
    agent = t3_agent.create_agent()
    res = agent.query("")
    assert res["status"] == "error"
    assert "Prompt cannot be empty" in res["message"]


def test_t3_smoke_test_function():
    """Verify automated smoke test script returns True."""
    assert t3_smoke.run_smoke_test() is True


@pytest.mark.asyncio
async def test_t3_service_healthz_and_query_endpoints():
    """Verify Cloud Run service HTTP endpoints."""
    transport = ASGITransport(app=t3_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Healthz check
        health = await client.get("/healthz")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"
        assert health.json()["service"] == "t3-cloud-run-agent"

        # 2. Query check with ping
        query_res = await client.post("/query", json={"prompt": "ping"})
        assert query_res.status_code == 200
        assert query_res.json()["response"] == "pong"
        assert query_res.json()["runtime"] == "cloud-run"

        # 3. Query check with live reasoning prompt
        live_res = await client.post("/query", json={"prompt": "Summarize this ticket"})
        assert live_res.status_code == 200
        assert "Processed query on Cloud Run" in live_res.json()["response"]
