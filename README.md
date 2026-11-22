# 🌐 Remote MCP Server

A production-ready, deployable **Remote Model Context Protocol (MCP)** server built with Python 3.12, **FastMCP**, and Starlette. It enables distributed team members to connect their AI assistants (Cursor, Claude Desktop, Antigravity, Cline, etc.) to a centralized, shared suite of tools, prompts, resources, and shared state over **Server-Sent Events (SSE)**.

---

## ✨ Features

- **🚀 SSE & HTTP Transport**: Native support for Server-Sent Events (`/sse`), compatible with all major MCP clients.
- **🔒 Flexible Multi-Method Authentication**:
  - `Authorization: Bearer <token>` header
  - `X-API-Key: <token>` header
  - URL Query parameter `?token=<token>` or `?api_key=<token>`
  - Optional Open/Development mode (auth disabled when no token configured)
- **🖥️ Live Interactive Dashboard**: Point your browser to `http://localhost:8000/` (or your deployed URL) to view live server status, endpoint details, and 1-click client configuration guides.
- **🩺 Unauthenticated Health Probes**: `/health` endpoint for Docker, Kubernetes, Render, Railway, AWS ALB, and GCP health checks.
- **🛠️ Built-in Starter Tools & State**:
  - **Diagnostics**: `ping`, `echo`, `get_server_status`
  - **Shared Team Notes**: `save_team_note`, `list_team_notes`, `get_team_note`, `search_team_notes`, `delete_team_note` (persistent JSON storage)
  - **Utilities**: Safe math expression evaluator (`calculate`), clean webpage text scraper (`fetch_webpage`), JSON dot-notation query (`query_json`)
- **📚 Resources & Prompts**: Team engineering handbook (`team://handbook`), daily standup generator (`daily_standup`), senior code review assistant (`code_review`), ADR generator (`architecture_decision_record`).
- **📦 Cloud Deployment Ready**: Includes `Dockerfile`, `docker-compose.yml`, `render.yaml`, `fly.toml`, and `railway.json`.

---

## 📁 Project Structure

```
remote_mcpserver/
├── src/
│   └── remote_mcpserver/
│       ├── __init__.py          # Exports create_app, create_server, main
│       ├── config.py            # Environment settings (Pydantic BaseSettings)
│       ├── auth.py              # Multi-token verifier & credential normalizer
│       ├── server.py            # FastMCP server, routes, dashboard & ASGI app
│       ├── resources.py         # MCP resources (team docs & handbook)
│       ├── prompts.py           # MCP prompt templates
│       └── tools/
│           ├── __init__.py      # Tool registration dispatcher
│           ├── diagnostics.py   # ping, echo, server_status
│           ├── team_notes.py    # Persistent shared team notes
│           └── utilities.py     # calculate, fetch_webpage, query_json
├── tests/
│   ├── __init__.py
│   └── test_server.py           # Automated test suite (100% passing)
├── main.py                      # Root execution entrypoint
├── Dockerfile                   # Optimized multi-stage Python 3.12 Dockerfile
├── docker-compose.yml           # Compose specification with persistent volume
├── render.yaml                  # 1-click blueprint for Render
├── fly.toml                     # Fly.io deployment config
├── railway.json                 # Railway deployment config
├── .env.example                 # Configuration environment template
└── pyproject.toml               # Package configuration & dependencies
```

---

## 🚀 Quickstart (Local)

### 1. Prerequisites
- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or standard `pip`

### 2. Setup Environment
```bash
# Clone the repository
git clone <repo-url>
cd remote_mcpserver

# Copy environment template
cp .env.example .env
```

### 3. Run the Server
Using `uv`:
```bash
uv run remote-mcpserver
# or
uv run python main.py
```

Using standard Python:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install .
uvicorn main:app --host 0.0.0.0 --port 8000
```

Visit **http://localhost:8000/** in your browser to view the interactive server dashboard.

### 4. Run Automated Tests
```bash
uv run pytest
```

---

## 🌐 Deploying to the Cloud

### Option 1: Docker / Docker Compose (Any VPS / DigitalOcean / EC2)

1. Build and run the container:
```bash
docker compose up -d --build
```
2. Verify the server is running:
```bash
curl http://localhost:8000/health
```

### Option 2: Render (Free Tier Compatible)

1. Push this repository to GitHub / GitLab.
2. In [Render Dashboard](https://dashboard.render.com), click **New + &rarr; Blueprint**.
3. Select your repository. Render will automatically read `render.yaml` and configure:
   - Build Command: `uv sync --frozen --no-dev`
   - Start Command: `uv run uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Persistent 1 GB disk for notes storage
   - Automatic HTTPS URL (e.g. `https://remote-mcpserver-xxxx.onrender.com`)

### Option 3: Railway

1. Install Railway CLI or connect via GitHub on [railway.app](https://railway.app).
2. Run `railway up` or import the repository.
3. Railway automatically detects `Dockerfile` and `railway.json`.
4. In Settings, set `AUTH_TOKEN` in the Variables tab.

### Option 4: Fly.io

1. Launch your app with Fly CLI:
```bash
fly launch
```
2. Set your authentication secret:
```bash
fly secrets set AUTH_TOKEN="your-secure-token"
```
3. Deploy:
```bash
fly deploy
```

---

## 👥 How Team Members Connect

Once deployed, provide your team members with:
1. Your server URL (e.g., `https://your-server.onrender.com/sse`)
2. Their authentication token (if `AUTH_TOKEN` is set)

### 1. Cursor
1. Go to **Settings &rarr; Features &rarr; MCP &rarr; Add New MCP Server**.
2. Configure:
   - **Name**: `team-remote`
   - **Type**: `sse`
   - **URL**: `https://your-server.onrender.com/sse?token=YOUR_TOKEN`

### 2. Claude Desktop
Add to your `claude_desktop_config.json`:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "team-remote": {
      "url": "https://your-server.onrender.com/sse",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### 3. Antigravity / Gemini CLI
Add to your settings or project MCP configuration:

```json
{
  "mcpServers": {
    "team-remote": {
      "url": "https://your-server.onrender.com/sse",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### 4. Cline / Roo Code (VS Code Extension)
In `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "team-remote": {
      "url": "https://your-server.onrender.com/sse",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### 5. Python Client
```python
import asyncio
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

async def main():
    async with Client(
        "https://your-server.onrender.com/sse",
        auth=BearerAuth("YOUR_TOKEN")
    ) as client:
        # List tools
        tools = await client.list_tools()
        print("Tools:", [t.name for t in tools])

        # Call a tool
        result = await client.call_tool("ping", {})
        print("Result:", result)

asyncio.run(main())
```

---

## 🔒 Configuration & Environment Variables

Create a `.env` file in the root directory:

| Variable | Default | Description |
|---|---|---|
| `SERVER_NAME` | `Remote MCP Server` | Display name of the server |
| `SERVER_VERSION` | `0.1.0` | Version string |
| `HOST` | `0.0.0.0` | Host address to bind |
| `PORT` | `8000` | Listening port (reads cloud `$PORT` automatically) |
| `TRANSPORT` | `sse` | MCP transport protocol (`sse` or `http`) |
| `AUTH_TOKEN` | `""` | Master Bearer token / API key. If empty, auth is disabled. |
| `AUTH_TOKENS` | `""` | Comma-separated list of additional member tokens |
| `DATA_DIR` | `./data` | Directory for persistent storage (team notes) |
| `CORS_ORIGINS` | `*` | Allowed CORS origins for web clients |
| `LOG_LEVEL` | `info` | Logging verbosity (`debug`, `info`, `warning`, `error`) |

---

## 🛠️ Adding Custom Tools

To add your own tools:
1. Open `src/remote_mcpserver/tools/utilities.py` (or create a new file in `tools/`).
2. Add your tool with the `@mcp.tool()` decorator:

```python
@mcp.tool(
    name="my_custom_tool",
    description="Explain what this tool does so AI models know when to call it."
)
def my_custom_tool(param1: str, count: int = 1) -> dict:
    # Your custom business logic here
    return {"status": "success", "result": param1 * count}
```

3. If creating a new file, register it in `src/remote_mcpserver/tools/__init__.py`.
4. Run `uv run pytest` to ensure tests continue passing.

---

## 📄 License
MIT License. Free to use and customize for personal or team projects.
