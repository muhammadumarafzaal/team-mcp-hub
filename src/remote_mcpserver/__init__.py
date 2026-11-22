from __future__ import annotations

import logging
from remote_mcpserver.config import Settings, settings
from remote_mcpserver.server import create_app, create_server

__all__ = ["create_app", "create_server", "Settings", "settings", "main"]


def main() -> None:
    """CLI entrypoint to run the Remote MCP Server with uvicorn."""
    import uvicorn

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("=" * 60)
    print(f"🚀 Starting {settings.SERVER_NAME} v{settings.SERVER_VERSION}")
    print(f"📡 Transport: {settings.TRANSPORT.upper()} (SSE Endpoint: http://{settings.HOST}:{settings.PORT}/sse)")
    print(f"🔒 Authentication: {'ENABLED' if settings.is_auth_enabled else 'DISABLED (Open Mode)'}")
    print(f"📊 Dashboard: http://{settings.HOST}:{settings.PORT}/")
    print(f"🩺 Health: http://{settings.HOST}:{settings.PORT}/health")
    print("=" * 60)

    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()
