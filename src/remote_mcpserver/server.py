from __future__ import annotations

import datetime
import logging
import time
from typing import Optional

from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.types import ASGIApp

from remote_mcpserver.auth import MultiAuthQueryMiddleware, build_token_verifier
from remote_mcpserver.config import Settings, settings as default_settings
from remote_mcpserver.prompts import register_prompts
from remote_mcpserver.resources import register_resources
from remote_mcpserver.tools import register_all_tools

logger = logging.getLogger(__name__)


def create_server(cfg: Optional[Settings] = None) -> FastMCP:
    """Create and configure the FastMCP instance with tools, resources, and custom routes."""
    config = cfg or default_settings
    start_time = time.time()

    # Configure authentication if tokens are present
    auth_verifier = build_token_verifier(config)

    mcp = FastMCP(
        name=config.SERVER_NAME,
        instructions=config.SERVER_INSTRUCTIONS,
        auth=auth_verifier,
    )

    # Register tools, resources, and prompts
    register_all_tools(mcp=mcp, start_time=start_time, data_dir=config.DATA_DIR)
    register_resources(mcp=mcp)
    register_prompts(mcp=mcp)

    # Custom Health Check Route (Unauthenticated for Docker/K8s/Cloud probes)
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        uptime = round(time.time() - start_time, 2)
        return JSONResponse({
            "status": "healthy",
            "server": config.SERVER_NAME,
            "version": config.SERVER_VERSION,
            "uptime_seconds": uptime,
            "auth_enabled": config.is_auth_enabled,
            "transport": config.TRANSPORT,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })

    # Machine-readable API Info endpoint
    @mcp.custom_route("/api/info", methods=["GET"])
    async def api_info(request: Request) -> JSONResponse:
        tools = await mcp.list_tools()
        resources = await mcp.list_resources()
        prompts = await mcp.list_prompts()
        return JSONResponse({
            "name": config.SERVER_NAME,
            "version": config.SERVER_VERSION,
            "auth_enabled": config.is_auth_enabled,
            "transport": config.TRANSPORT,
            "tools": [{"name": t.name, "description": t.description} for t in tools],
            "resources": [{"uri": str(r.uri), "name": r.name} for r in resources],
            "prompts": [{"name": p.name, "description": p.description} for p in prompts],
        })

    # Interactive Dashboard / Landing Page
    @mcp.custom_route("/", methods=["GET"])
    async def root_dashboard(request: Request) -> HTMLResponse | JSONResponse:
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header:
            return await api_info(request)

        tools = await mcp.list_tools()
        tool_cards = "".join(
            f"""
            <div class="tool-card">
                <div class="tool-name"><code>{t.name}</code></div>
                <div class="tool-desc">{t.description or 'No description provided.'}</div>
            </div>
            """
            for t in tools
        )

        auth_badge = (
            '<span class="badge badge-success">🔒 Auth Required (Token)</span>'
            if config.is_auth_enabled
            else '<span class="badge badge-warning">🔓 Open / No Auth</span>'
        )

        host_header = request.headers.get("host", f"localhost:{config.PORT}")
        scheme = "https" if request.url.scheme == "https" or "render" in host_header or "railway" in host_header else request.url.scheme
        base_url = f"{scheme}://{host_header}"
        sse_url = f"{base_url}/sse"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.SERVER_NAME}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --primary: #38bdf8;
            --primary-hover: #0ea5e9;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --success: #22c55e;
            --warning: #f59e0b;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem 1rem;
        }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--border);
            margin-bottom: 2rem;
        }}
        h1 {{ font-size: 2.25rem; font-weight: 700; color: var(--text); margin-bottom: 0.5rem; }}
        p.subtitle {{ color: var(--text-muted); font-size: 1.1rem; }}
        .status-bar {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .badge-success {{ background: rgba(34, 197, 94, 0.15); color: var(--success); border: 1px solid rgba(34, 197, 94, 0.3); }}
        .badge-warning {{ background: rgba(245, 158, 11, 0.15); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.3); }}
        .badge-info {{ background: rgba(56, 189, 248, 0.15); color: var(--primary); border: 1px solid rgba(56, 189, 248, 0.3); }}
        
        section {{
            background: var(--surface);
            border-radius: 0.75rem;
            border: 1px solid var(--border);
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        h2 {{ font-size: 1.35rem; margin-bottom: 1rem; color: var(--primary); display: flex; align-items: center; gap: 0.5rem; }}
        
        .endpoint-box {{
            background: #090d16;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 0.85rem 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: monospace;
            font-size: 0.95rem;
            color: #38bdf8;
            margin-bottom: 1rem;
            word-break: break-all;
        }}
        
        pre {{
            background: #090d16;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 1rem;
            overflow-x: auto;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.85rem;
            color: #e2e8f0;
            margin-bottom: 1rem;
        }}

        .tools-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}
        .tool-card {{
            background: #090d16;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 1rem;
            transition: border-color 0.2s;
        }}
        .tool-card:hover {{ border-color: var(--primary); }}
        .tool-name code {{
            color: var(--primary);
            font-size: 0.95rem;
            font-weight: 600;
        }}
        .tool-desc {{
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 0.4rem;
        }}
        
        .tab-buttons {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}
        .tab-btn {{
            background: var(--surface-hover);
            color: var(--text-muted);
            border: 1px solid var(--border);
            padding: 0.45rem 0.9rem;
            border-radius: 0.4rem;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.85rem;
        }}
        .tab-btn.active {{
            background: var(--primary);
            color: #0f172a;
            border-color: var(--primary);
            font-weight: 600;
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        
        footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            padding-top: 1rem;
        }}
        a {{ color: var(--primary); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌐 {config.SERVER_NAME}</h1>
            <p class="subtitle">{config.SERVER_INSTRUCTIONS}</p>
            <div class="status-bar">
                <span class="badge badge-success">🟢 Server Online</span>
                <span class="badge badge-info">Transport: {config.TRANSPORT.upper()}</span>
                {auth_badge}
                <span class="badge badge-info">Version: {config.SERVER_VERSION}</span>
            </div>
        </header>

        <section>
            <h2>📡 Client Connection Endpoint</h2>
            <p style="color: var(--text-muted); margin-bottom: 0.75rem;">
                Connect any MCP-compatible agent or client to this Server-Sent Events (SSE) endpoint:
            </p>
            <div class="endpoint-box">
                <span>{sse_url}</span>
            </div>
        </section>

        <section>
            <h2>💻 How Team Members Connect</h2>
            <div class="tab-buttons">
                <button class="tab-btn active" onclick="showTab('cursor')">Cursor</button>
                <button class="tab-btn" onclick="showTab('claude')">Claude Desktop</button>
                <button class="tab-btn" onclick="showTab('antigravity')">Antigravity / Gemini CLI</button>
                <button class="tab-btn" onclick="showTab('cline')">Cline / VS Code</button>
                <button class="tab-btn" onclick="showTab('python')">Python Client</button>
            </div>

            <!-- Cursor Tab -->
            <div id="tab-cursor" class="tab-content active">
                <p style="color: var(--text-muted); margin-bottom: 0.5rem;">
                    In Cursor: <b>Settings &rarr; Features &rarr; MCP &rarr; Add New MCP Server</b>
                </p>
                <pre><code>Name: remote-mcp
Type: sse
URL:  {sse_url}</code></pre>
                <p style="color: var(--text-muted); font-size: 0.85rem;">
                    <i>Note: If authentication is enabled, pass your token in the URL query string: <code>{sse_url}?token=YOUR_TOKEN</code> or configure headers.</i>
                </p>
            </div>

            <!-- Claude Tab -->
            <div id="tab-claude" class="tab-content">
                <p style="color: var(--text-muted); margin-bottom: 0.5rem;">
                    Add to your <code>claude_desktop_config.json</code>:
                </p>
                <pre><code>{{
  "mcpServers": {{
    "team-remote": {{
      "url": "{sse_url}",
      "headers": {{
        "Authorization": "Bearer YOUR_SECRET_TOKEN"
      }}
    }}
  }}
}}</code></pre>
            </div>

            <!-- Antigravity Tab -->
            <div id="tab-antigravity" class="tab-content">
                <p style="color: var(--text-muted); margin-bottom: 0.5rem;">
                    Add to your MCP settings or plugin configuration:
                </p>
                <pre><code>{{
  "mcpServers": {{
    "team-remote": {{
      "url": "{sse_url}",
      "headers": {{
        "Authorization": "Bearer YOUR_SECRET_TOKEN"
      }}
    }}
  }}
}}</code></pre>
            </div>

            <!-- Cline Tab -->
            <div id="tab-cline" class="tab-content">
                <p style="color: var(--text-muted); margin-bottom: 0.5rem;">
                    In Cline (VS Code), add to <code>cline_mcp_settings.json</code>:
                </p>
                <pre><code>{{
  "mcpServers": {{
    "team-remote": {{
      "url": "{sse_url}",
      "headers": {{
        "Authorization": "Bearer YOUR_SECRET_TOKEN"
      }}
    }}
  }}
}}</code></pre>
            </div>

            <!-- Python Tab -->
            <div id="tab-python" class="tab-content">
                <p style="color: var(--text-muted); margin-bottom: 0.5rem;">
                    Connect programmatically using the FastMCP Client:
                </p>
                <pre><code>import asyncio
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

async def main():
    async with Client(
        "{sse_url}",
        auth=BearerAuth("YOUR_SECRET_TOKEN")
    ) as client:
        tools = await client.list_tools()
        print("Connected tools:", [t.name for t in tools])
        result = await client.call_tool("ping", {{}})
        print("Ping result:", result)

asyncio.run(main())</code></pre>
            </div>
        </section>

        <section>
            <h2>🛠️ Available Tools ({len(tools)})</h2>
            <div class="tools-grid">
                {tool_cards}
            </div>
        </section>

        <footer>
            <p>Remote MCP Server &bull; <a href="/health">Health Endpoint</a> &bull; <a href="/api/info">API Info</a></p>
        </footer>
    </div>

    <script>
        function showTab(id) {{
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById('tab-' + id).classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>
"""
        return HTMLResponse(content=html_content)

    return mcp


def create_app(cfg: Optional[Settings] = None) -> ASGIApp:
    """Build and return the production Starlette ASGI application.

    Includes FastMCP SSE transport, MultiAuthQueryMiddleware, and CORSMiddleware.
    """
    config = cfg or default_settings
    server = create_server(config)

    # FastMCP ASGI application
    raw_app = server.http_app(transport=config.TRANSPORT)

    # 1. MultiAuthQueryMiddleware intercepts query params and X-API-Key and standardizes Authorization headers
    app_with_auth = MultiAuthQueryMiddleware(raw_app)

    # 2. CORS Middleware allows cross-origin requests from web-based LLM clients
    app_with_cors = CORSMiddleware(
        app_with_auth,
        allow_origins=config.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app_with_cors
