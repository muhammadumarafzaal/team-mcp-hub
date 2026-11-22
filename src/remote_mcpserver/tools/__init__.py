from __future__ import annotations

from pathlib import Path
from fastmcp import FastMCP

from remote_mcpserver.tools.diagnostics import register_diagnostics_tools
from remote_mcpserver.tools.team_notes import register_team_notes_tools
from remote_mcpserver.tools.utilities import register_utility_tools


def register_all_tools(mcp: FastMCP, start_time: float, data_dir: Path) -> None:
    """Register all server tools on the FastMCP instance."""
    register_diagnostics_tools(mcp=mcp, start_time=start_time)
    register_team_notes_tools(mcp=mcp, data_dir=data_dir)
    register_utility_tools(mcp=mcp)
