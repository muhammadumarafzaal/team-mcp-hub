from __future__ import annotations

import datetime
import os
import platform
import sys
import time
from typing import Any, Dict

from fastmcp import FastMCP


def register_diagnostics_tools(mcp: FastMCP, start_time: float) -> None:
    """Register diagnostic and health checking tools on the FastMCP instance."""

    @mcp.tool(
        name="ping",
        description="Health-check tool. Returns 'pong' with current server timestamp and uptime.",
    )
    def ping() -> Dict[str, Any]:
        """Verify the remote MCP server is alive and responding."""
        uptime = round(time.time() - start_time, 2)
        return {
            "status": "pong",
            "server_time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "uptime_seconds": uptime,
        }

    @mcp.tool(
        name="echo",
        description="Echoes back any input text. Useful for testing tool arguments and connectivity.",
    )
    def echo(message: str) -> Dict[str, Any]:
        """Echo a message back to the caller."""
        return {
            "echo": message,
            "received_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "length": len(message),
        }

    @mcp.tool(
        name="get_server_status",
        description="Returns detailed runtime information, OS platform, Python version, and server stats.",
    )
    def get_server_status() -> Dict[str, Any]:
        """Retrieve operational statistics and environment details from the remote server."""
        uptime = round(time.time() - start_time, 2)
        return {
            "server_name": mcp.name,
            "status": "online",
            "uptime_seconds": uptime,
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
            "process_id": os.getpid(),
            "server_time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
