"""Entrypoint for running the Remote MCP Server."""

from remote_mcpserver import create_app, main, settings

# ASGI app instance for production uvicorn/gunicorn runners:
# Example: uvicorn main:app --host 0.0.0.0 --port 8000
app = create_app(settings)

if __name__ == "__main__":
    main()
