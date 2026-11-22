"""Alternative direct server entrypoint for FastMCP Cloud / FastMCP Gateway."""

import sys
from pathlib import Path

# Ensure 'src' is discoverable when run in fresh containers without editable package install
_root_dir = Path(__file__).resolve().parent
_src_dir = _root_dir / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from remote_mcpserver import create_app, create_server, settings

# FastMCP server instance
mcp = create_server(settings)
server = mcp

# ASGI app instance
app = create_app(settings)
