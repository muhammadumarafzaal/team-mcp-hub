"""Entrypoint for running the Remote MCP Server."""

from remote_mcpserver import create_app, create_server, main, settings

# FastMCP server instance for FastMCP Cloud / CLI:
mcp = create_server(settings)
server = mcp

# ASGI app instance for production uvicorn/gunicorn runners:
app = create_app(settings)

if __name__ == "__main__":
    main()
