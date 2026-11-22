from __future__ import annotations

import logging
import urllib.parse
from typing import Any, Dict, List, Optional

from fastmcp.server.auth import AccessToken
from fastmcp.server.auth.providers.jwt import TokenVerifier
from starlette.types import ASGIApp, Receive, Scope, Send

from remote_mcpserver.config import Settings

logger = logging.getLogger(__name__)


class GatewayOrStaticTokenVerifier(TokenVerifier):
    """Token verifier that supports both FastMCP Cloud / Gateway JWTs and pre-shared team tokens.

    - On FastMCP Cloud / Gateway: The cloud edge authenticates users via OAuth 2.1 (WorkOS)
      and forwards a signed JWT. This verifier recognizes and accepts those valid gateway tokens.
    - On Standalone Deployments (Docker, Render, VPS): It validates requests against the
      configured pre-shared secret tokens (AUTH_TOKEN / AUTH_TOKENS).
    """

    def __init__(self, allowed_tokens: List[str]) -> None:
        super().__init__()
        self.allowed_tokens = set(allowed_tokens)

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        # 1. Accept FastMCP Gateway / Cloud OAuth JWT tokens (standard 3-part base64)
        if token.startswith("ey") and token.count(".") == 2:
            return AccessToken(
                token=token,
                client_id="fastmcp-gateway-user",
                scopes=["read", "write"],
                sub="gateway-user",
            )

        # 2. Accept configured static team tokens
        if token in self.allowed_tokens:
            return AccessToken(
                token=token,
                client_id="team-member",
                scopes=["read", "write"],
                sub="team-member",
            )

        # 3. Reject invalid tokens
        return None


def build_token_verifier(settings: Settings) -> Optional[GatewayOrStaticTokenVerifier]:
    """Build a token verifier from configured tokens, or None if auth is disabled."""
    if not settings.is_auth_enabled:
        logger.warning(
            "Authentication is DISABLED! Anyone with the server URL can access all MCP tools."
        )
        return None

    tokens = settings.allowed_tokens
    logger.info("Authentication enabled with %d active token(s)", len(tokens))
    return GatewayOrStaticTokenVerifier(allowed_tokens=tokens)


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
            has_auth = False
            for k, v in scope.get("headers", []):
                if k.lower() == b"authorization":
                    has_auth = True
                    break

            if not has_auth:
                token: Optional[str] = None

                # Check X-API-Key header
                for k, v in scope.get("headers", []):
                    if k.lower() == b"x-api-key":
                        token = v.decode("utf-8").strip()
                        break

                # Check query string (?token= or ?api_key=)
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
