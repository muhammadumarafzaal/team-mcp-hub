from __future__ import annotations

import logging
import urllib.parse
from typing import Any, Dict, Optional

from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from starlette.types import ASGIApp, Receive, Scope, Send

from remote_mcpserver.config import Settings

logger = logging.getLogger(__name__)


def build_token_verifier(settings: Settings) -> Optional[StaticTokenVerifier]:
    """Build a token verifier from configured tokens, or None if auth is disabled."""
    if not settings.is_auth_enabled:
        logger.warning(
            "Authentication is DISABLED! Anyone with the server URL can access all MCP tools."
        )
        return None

    tokens_dict: Dict[str, Dict[str, Any]] = {}
    for i, token in enumerate(settings.allowed_tokens):
        client_id = f"team-member-{i + 1}"
        tokens_dict[token] = {
            "client_id": client_id,
            "scopes": ["read", "write"],
            "sub": client_id,
        }

    logger.info("Authentication enabled with %d active token(s)", len(tokens_dict))
    return StaticTokenVerifier(tokens=tokens_dict)


class MultiAuthQueryMiddleware:
    """ASGI Middleware to normalize authentication credentials across different client types.

    MCP clients connect in different ways:
    1. Standard headers: `Authorization: Bearer <token>`
    2. API Key headers: `X-API-Key: <token>`
    3. URL Query parameters: `?token=<token>` or `?api_key=<token>`

    This middleware intercepts HTTP requests and ensures the standard
    `Authorization: Bearer <token>` header is present in the ASGI scope,
    enabling all MCP clients to work seamlessly with FastMCP.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))

            # 1. Check if Authorization header is already present
            has_auth = False
            for k, v in scope.get("headers", []):
                if k.lower() == b"authorization":
                    has_auth = True
                    break

            if not has_auth:
                token: Optional[str] = None

                # 2. Check X-API-Key header
                for k, v in scope.get("headers", []):
                    if k.lower() == b"x-api-key":
                        token = v.decode("utf-8").strip()
                        break

                # 3. Check query string (?token= or ?api_key=)
                if not token:
                    query_string = scope.get("query_string", b"").decode("utf-8")
                    if query_string:
                        params = urllib.parse.parse_qs(query_string)
                        token = (
                            params.get("token", [None])[0]
                            or params.get("api_key", [None])[0]
                        )

                if token:
                    new_headers = list(scope.get("headers", []))
                    new_headers.append(
                        (b"authorization", f"Bearer {token}".encode("utf-8"))
                    )
                    scope["headers"] = new_headers

        await self.app(scope, receive, send)
