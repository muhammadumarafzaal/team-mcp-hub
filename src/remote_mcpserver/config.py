from __future__ import annotations

import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the Remote MCP Server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server Info
    SERVER_NAME: str = Field(default="Remote MCP Server", description="Name of the MCP server")
    SERVER_VERSION: str = Field(default="0.1.0", description="Server version")
    SERVER_INSTRUCTIONS: str = Field(
        default="Remote MCP server providing shared team tools, notes, diagnostics, and web utilities.",
        description="Instructions provided to LLM clients",
    )

    # Network / Binding
    HOST: str = Field(default="0.0.0.0", description="Host to bind server")
    PORT: int = Field(default=8000, description="Port to listen on (also reads $PORT)")

    # MCP Protocol Transport
    TRANSPORT: str = Field(
        default="sse",
        description="MCP transport: 'sse' (Server-Sent Events) or 'http' (Streamable HTTP)",
    )

    # Authentication
    # If AUTH_TOKEN is non-empty, requests must supply this Bearer token or API key.
    AUTH_TOKEN: str = Field(
        default="",
        description="Primary Bearer token / API key required for client access. If empty, auth is disabled.",
    )
    # Comma-separated list of additional tokens for team members
    AUTH_TOKENS: str = Field(
        default="",
        description="Optional comma-separated list of additional valid tokens for team members.",
    )

    # Storage
    DATA_DIR: Path = Field(
        default=Path("./data"),
        description="Directory for persistent data storage (e.g., team notes)",
    )

    # CORS
    CORS_ORIGINS: str = Field(
        default="*",
        description="Comma-separated allowed CORS origins or '*' to allow all.",
    )

    # Logging
    LOG_LEVEL: str = Field(default="info", description="Logging level: debug, info, warning, error")

    @property
    def is_auth_enabled(self) -> bool:
        """Return True if token authentication is required."""
        return bool(self.AUTH_TOKEN.strip() or self.AUTH_TOKENS.strip())

    @property
    def allowed_tokens(self) -> List[str]:
        """Return list of all configured valid authentication tokens."""
        tokens: List[str] = []
        if self.AUTH_TOKEN.strip():
            tokens.append(self.AUTH_TOKEN.strip())
        if self.AUTH_TOKENS.strip():
            for t in self.AUTH_TOKENS.split(","):
                clean = t.strip()
                if clean and clean not in tokens:
                    tokens.append(clean)
        return tokens

    @property
    def cors_origins_list(self) -> List[str]:
        """Return list of origins allowed by CORS."""
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


# Global settings instance
settings = Settings(
    # Handle cloud hosts that inject PORT directly as string
    PORT=int(os.environ.get("PORT", 8000))
)
