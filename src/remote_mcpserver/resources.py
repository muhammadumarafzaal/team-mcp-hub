from __future__ import annotations

from fastmcp import FastMCP


def register_resources(mcp: FastMCP) -> None:
    """Register MCP resources on the FastMCP instance."""

    @mcp.resource(
        "team://handbook",
        name="Team Engineering Handbook",
        description="Guidelines, coding standards, and best practices for the team.",
    )
    def team_handbook() -> str:
        return """# Team Engineering Handbook

## 1. Collaboration & Communication
- Keep shared notes up to date using the `save_team_note` tool.
- Use asynchronous communication for updates, questions, and decisions.

## 2. Code Quality & Standards
- Keep functions small, modular, and well-typed.
- Every new feature must include automated tests.
- Always review code for security risks (never store secrets in plain text).

## 3. Deployment & Production
- All cloud services must expose a `/health` endpoint for readiness probes.
- Authentication tokens must be configured in production via environment variables.
"""

    @mcp.resource(
        "team://server-docs",
        name="Remote MCP Server Documentation",
        description="Server endpoints, transport protocols, and client integration guide.",
    )
    def server_docs() -> str:
        return """# Remote MCP Server Documentation

## Endpoints:
- `GET /sse`: Server-Sent Events MCP endpoint (connect MCP clients here).
- `POST /messages/`: JSON-RPC transport endpoint for active SSE sessions.
- `GET /health`: Health-check endpoint for container orchestration.
- `GET /`: Interactive web dashboard and client setup helper.
- `GET /api/info`: Machine-readable server capabilities summary.

## Client Header Authentication:
- `Authorization: Bearer <AUTH_TOKEN>`
- `X-API-Key: <AUTH_TOKEN>`
- Or query parameter: `?token=<AUTH_TOKEN>`
"""
