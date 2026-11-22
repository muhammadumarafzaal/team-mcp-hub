# ==============================================================================
# Production Dockerfile for Remote MCP Server
# ==============================================================================

FROM python:3.12-slim AS builder

# Install uv for ultra-fast dependency resolution and installation
COPY --from=ghcr.io/astral-sh/uv:0.12.14 /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies first (leverage Docker layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy application source code
COPY src/ ./src/
COPY main.py README.md ./

# Install project
RUN uv sync --frozen --no-dev

# ------------------------------------------------------------------------------
# Final Lightweight Runtime Image
# ------------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser -m -d /home/mcpuser mcpuser

# Copy virtualenv and app from builder
COPY --from=builder --chown=mcpuser:mcpuser /app /app

# Place virtual environment in PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DATA_DIR=/app/data

# Create data directory with correct ownership
RUN mkdir -p /app/data && chown -R mcpuser:mcpuser /app/data

USER mcpuser

# Expose server port
EXPOSE 8000

# Healthcheck probe using python standard library
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request, os; port = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health')" || exit 1

# Start server using uvicorn via shell to expand $PORT dynamically
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
