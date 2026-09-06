"""
Unit tests for IDP CLI client.
"""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from cli.idp.main import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "IDP CLI" in result.output


def test_cli_login_success():
    runner = CliRunner()
    with patch("httpx.Client.post") as mock_post, patch("cli.idp.main.save_session") as mock_save:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {"access_token": "mock-jwt-token"}
        mock_post.return_value = mock_res

        result = runner.invoke(
            cli,
            [
                "login",
                "--username",
                "admin_gov",
                "--password",
                "AdminPass123!",
                "--url",
                "http://test",
            ],
        )
        assert result.exit_code == 0
        assert "Successfully authenticated" in result.output
        mock_save.assert_called_once()


def test_cli_list_templates():
    runner = CliRunner()
    with patch("cli.idp.main.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = [
            {
                "template_id": "t1-agent-engine",
                "template_version": "2.0.0",
                "display_name": "Agent Engine",
                "cost_tier": "low",
            }
        ]
        mock_client.get.return_value = mock_res
        mock_get_client.return_value = (mock_client, "http://test")

        result = runner.invoke(cli, ["templates", "list"])
        assert result.exit_code == 0
        assert "t1-agent-engine" in result.output


def test_cli_create_request():
    runner = CliRunner()
    with patch("cli.idp.main.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_res = MagicMock()
        mock_res.status_code = 202
        mock_res.json.return_value = {
            "request_id": "req-123",
            "deployment_id": "dep-456",
            "status": "DISPATCHED",
        }
        mock_client.post.return_value = mock_res
        mock_get_client.return_value = (mock_client, "http://test")

        result = runner.invoke(
            cli,
            [
                "requests",
                "create",
                "--template",
                "t1-agent-engine",
                "--inputs-json",
                '{"agent_name": "cli-agent"}',
            ],
        )
        assert result.exit_code == 0
        assert "req-123" in result.output


def test_cli_governance_inspect():
    runner = CliRunner()
    with patch("cli.idp.main.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "passed": True,
            "action_taken": "allowed",
            "violations": [],
            "processed_text": "Safe text",
        }
        mock_client.post.return_value = mock_res
        mock_get_client.return_value = (mock_client, "http://test")

        result = runner.invoke(cli, ["governance", "inspect", "Hello agent"])
        assert result.exit_code == 0
        assert "Passed:       True" in result.output


def test_cli_deployment_config():
    runner = CliRunner()
    with patch("cli.idp.main.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "deployment_id": "dep-123",
            "safe_config": {
                "deployment_id": "dep-123",
                "workspace": "ws-dev",
                "environment": "dev",
                "project_id": "mybrightday-dev",
                "template_id": "t1-agent-engine",
                "template_version": "2.0.0",
                "status": "ACTIVE",
                "outputs": {
                    "runtime_sa_email": "sa-t1-xyz@mybrightday-dev.iam.gserviceaccount.com",
                    "model_name": "gemini-2.5-flash",
                    "region": "us-central1",
                },
            },
        }
        mock_client.get.return_value = mock_res
        mock_get_client.return_value = (mock_client, "http://test")

        result = runner.invoke(cli, ["deployments", "config", "dep-123"])
        assert result.exit_code == 0
        assert "dep-123" in result.output
        assert "sa-t1-xyz" in result.output
        assert "gemini-2.5-flash" in result.output
