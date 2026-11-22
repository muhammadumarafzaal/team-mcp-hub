import json
import pytest
from pathlib import Path
from starlette.testclient import TestClient

from remote_mcpserver.config import Settings
from remote_mcpserver.server import create_app, create_server


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Create isolated settings with authentication enabled."""
    return Settings(
        SERVER_NAME="Test Remote MCP",
        SERVER_VERSION="0.1.0",
        HOST="127.0.0.1",
        PORT=8000,
        TRANSPORT="sse",
        AUTH_TOKEN="test-secret-key-123",
        AUTH_TOKENS="member-key-456",
        DATA_DIR=tmp_path / "data",
    )


@pytest.fixture
def open_settings(tmp_path: Path) -> Settings:
    """Create isolated settings with authentication disabled."""
    return Settings(
        SERVER_NAME="Open Remote MCP",
        SERVER_VERSION="0.1.0",
        HOST="127.0.0.1",
        PORT=8000,
        TRANSPORT="sse",
        AUTH_TOKEN="",
        AUTH_TOKENS="",
        DATA_DIR=tmp_path / "data",
    )


def test_health_check(test_settings: Settings):
    app = create_app(test_settings)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["server"] == "Test Remote MCP"
    assert data["auth_enabled"] is True


def test_root_dashboard_html(test_settings: Settings):
    app = create_app(test_settings)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Test Remote MCP" in response.text
    assert "Client Connection Endpoint" in response.text


def test_root_dashboard_json(test_settings: Settings):
    app = create_app(test_settings)
    client = TestClient(app)
    response = client.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Remote MCP"
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "ping" in tool_names
    assert "save_team_note" in tool_names
    assert "calculate" in tool_names


def test_api_info(test_settings: Settings):
    app = create_app(test_settings)
    client = TestClient(app)
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Remote MCP"
    assert len(data["tools"]) >= 6
    assert len(data["resources"]) >= 2
    assert len(data["prompts"]) >= 3


def test_auth_rejection(test_settings: Settings):
    app = create_app(test_settings)
    client = TestClient(app)
    with client:
        # No auth provided -> 401
        with client.stream("GET", "/sse") as resp:
            assert resp.status_code == 401

        # Invalid auth provided -> 401
        with client.stream("GET", "/sse", headers={"Authorization": "Bearer bad-token"}) as resp:
            assert resp.status_code == 401


def test_auth_acceptance_bearer_header(test_settings: Settings):
    app = create_app(test_settings)
    client = TestClient(app)
    with client:
        with client.stream(
            "GET", "/sse", headers={"Authorization": "Bearer test-secret-key-123"}
        ) as resp:
            assert resp.status_code == 200

        with client.stream(
            "GET", "/sse", headers={"Authorization": "Bearer member-key-456"}
        ) as resp:
            assert resp.status_code == 200


def test_auth_acceptance_x_api_key(test_settings: Settings):
    app = create_app(test_settings)
    client = TestClient(app)
    with client:
        with client.stream("GET", "/sse", headers={"X-API-Key": "test-secret-key-123"}) as resp:
            assert resp.status_code == 200


def test_auth_acceptance_query_param(test_settings: Settings):
    app = create_app(test_settings)
    client = TestClient(app)
    with client:
        with client.stream("GET", "/sse?token=test-secret-key-123") as resp:
            assert resp.status_code == 200

        with client.stream("GET", "/sse?api_key=member-key-456") as resp:
            assert resp.status_code == 200


def test_open_server_no_auth(open_settings: Settings):
    app = create_app(open_settings)
    client = TestClient(app)
    with client:
        with client.stream("GET", "/sse") as resp:
            assert resp.status_code == 200


def test_tools_execution(test_settings: Settings):
    import asyncio
    from fastmcp import Client

    async def _run():
        server = create_server(test_settings)
        async with Client(server) as client:
            # Test ping
            res_ping = await client.call_tool("ping", {})
            assert res_ping.structured_content["status"] == "pong"

            # Test echo
            res_echo = await client.call_tool("echo", {"message": "Hello Team"})
            assert res_echo.structured_content["echo"] == "Hello Team"

            # Test calculate
            res_calc = await client.call_tool("calculate", {"expression": "2 * (10 + 5) + sqrt(16)"})
            assert res_calc.structured_content["result"] == 34.0

            # Test calculate division by zero
            res_zero = await client.call_tool("calculate", {"expression": "10 / 0"})
            assert res_zero.structured_content["status"] == "error"

            # Test team notes: save, list, get, delete
            save_res = await client.call_tool(
                "save_team_note",
                {
                    "title": "Welcome Guide",
                    "content": "Welcome to our shared remote MCP server!",
                    "author": "Admin",
                    "tags": ["guide", "onboarding"],
                },
            )
            assert save_res.structured_content["success"] is True

            list_res = await client.call_tool("list_team_notes", {"tag": "guide"})
            assert list_res.structured_content["count"] == 1
            assert list_res.structured_content["notes"][0]["title"] == "Welcome Guide"

            get_res = await client.call_tool("get_team_note", {"title": "Welcome Guide"})
            assert get_res.structured_content["found"] is True
            assert get_res.structured_content["note"]["content"] == "Welcome to our shared remote MCP server!"

            del_res = await client.call_tool("delete_team_note", {"title": "Welcome Guide"})
            assert del_res.structured_content["deleted"] is True

            # Test query_json
            sample_json = json.dumps({"project": {"name": "remote-mcpserver", "tags": ["mcp", "fastmcp"]}})
            q_res = await client.call_tool("query_json", {"json_string": sample_json, "query_path": "project.tags[0]"})
            assert q_res.structured_content["result"] == "mcp"

    asyncio.run(_run())
