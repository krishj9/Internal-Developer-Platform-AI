"""
Unit tests for the Math Reasoning Agent application workload.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_workload_dir = Path(__file__).parent.parent
if str(_workload_dir) not in sys.path:
    sys.path.insert(0, str(_workload_dir))


def _load_module(mod_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module specification from {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


tools_mod = _load_module("math_tools_mod", _workload_dir / "math_tools.py")
agent_mod = _load_module("math_agent_mod", _workload_dir / "math_agent.py")
deploy_mod = _load_module("math_deploy_mod", _workload_dir / "deploy.py")

add = tools_mod.add
subtract = tools_mod.subtract
multiply = tools_mod.multiply
divide = tools_mod.divide
MATH_TOOL_REGISTRY = tools_mod.MATH_TOOL_REGISTRY
MathReasoningAgent = agent_mod.MathReasoningAgent
create_agent = agent_mod.create_agent
deploy_to_vertex_ai = deploy_mod.deploy_to_vertex_ai


def test_direct_arithmetic_tools():
    assert add(10, 5) == 15.0
    assert subtract(20, 8) == 12.0
    assert multiply(6, 7) == 42.0
    assert divide(50, 5) == 10.0


def test_divide_by_zero_raises_value_error():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)


def test_tool_registry_mapping():
    assert "add" in MATH_TOOL_REGISTRY
    assert "subtract" in MATH_TOOL_REGISTRY
    assert "multiply" in MATH_TOOL_REGISTRY
    assert "divide" in MATH_TOOL_REGISTRY
    assert MATH_TOOL_REGISTRY["multiply"](3, 4) == 12.0


def test_agent_ping_health_check():
    agent = MathReasoningAgent()
    res = agent.query("ping")
    assert res["status"] == "success"
    assert res["response"] == "pong"


def test_agent_multi_step_math_reasoning():
    agent = MathReasoningAgent()
    # Prompt requested by user: "Add 200 to 423 and subtract 98 from it"
    prompt = "Add 200 to 423 and subtract 98 from it"
    res = agent.query(prompt)

    assert res["status"] == "success"
    assert res["result_value"] == 525.0
    assert len(res["tool_calls"]) == 2

    # Step 1: add(200, 423) -> 623
    assert res["tool_calls"][0]["tool"] == "add"
    assert res["tool_calls"][0]["args"]["a"] == 200.0
    assert res["tool_calls"][0]["args"]["b"] == 423.0
    assert res["tool_calls"][0]["output"] == 623.0

    # Step 2: subtract(623, 98) -> 525
    assert res["tool_calls"][1]["tool"] == "subtract"
    assert res["tool_calls"][1]["args"]["a"] == 623.0
    assert res["tool_calls"][1]["args"]["b"] == 98.0
    assert res["tool_calls"][1]["output"] == 525.0

    assert "525" in res["final_answer"]


def test_agent_multiply_and_add():
    agent = MathReasoningAgent()
    prompt = "Multiply 15 by 8 and add 40"
    res = agent.query(prompt)

    assert res["status"] == "success"
    assert res["result_value"] == 160.0
    assert len(res["tool_calls"]) == 2
    assert res["tool_calls"][0]["tool"] == "multiply"
    assert res["tool_calls"][0]["output"] == 120.0
    assert res["tool_calls"][1]["tool"] == "add"
    assert res["tool_calls"][1]["output"] == 160.0


def test_agent_divide_by_zero_safety():
    agent = MathReasoningAgent()
    res = agent.query("divide 100 by 0")
    assert res["status"] == "error"
    assert "Division by zero" in res["message"]
    assert res["tool_calls"][0]["tool"] == "divide"


def test_deploy_dry_run_simulation():
    sample_config = {
        "deployment_id": "dep-unit-test",
        "project_id": "mybrightday-dev",
        "region": "us-central1",
        "staging_bucket": "idp-state-mybrightday-dev",
        "runtime_service_account": "sa-t1-test@mybrightday-dev.iam.gserviceaccount.com",
        "model_name": "gemini-2.5-flash",
    }
    resource = deploy_to_vertex_ai(sample_config, dry_run=True)
    assert "dep-unit" in resource
    assert "reasoningEngines" in resource
