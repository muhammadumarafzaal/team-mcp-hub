from __future__ import annotations

import ast
import json
import logging
import math
import operator
import re
from typing import Any, Dict

from fastmcp import FastMCP
import httpx

logger = logging.getLogger(__name__)

# Safe math operators and functions
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval(node: ast.AST) -> Any:
    """Evaluate an AST expression node securely without allowing code execution."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Constant type {type(node.value).__name__} is not allowed")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise ValueError(f"Operator {op_type.__name__} is not allowed")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise ValueError(f"Unary operator {op_type.__name__} is not allowed")
        return OPERATORS[op_type](_safe_eval(node.operand))
    elif isinstance(node, ast.Name):
        if node.id in FUNCTIONS:
            return FUNCTIONS[node.id]
        raise ValueError(f"Identifier '{node.id}' is not recognized")
    elif isinstance(node, ast.Call):
        func = _safe_eval(node.func)
        args = [_safe_eval(arg) for arg in node.args]
        return func(*args)
    raise ValueError(f"Expression element '{type(node).__name__}' is not permitted")


def register_utility_tools(mcp: FastMCP) -> None:
    """Register web, calculation, and data utility tools."""

    @mcp.tool(
        name="calculate",
        description="Safely evaluate a mathematical expression (e.g., '(25 * 4) / 5 + sqrt(144) + pi'). Supports basic arithmetic and standard math functions.",
    )
    def calculate(expression: str) -> Dict[str, Any]:
        """Safely compute mathematical formulas."""
        clean_expr = expression.strip()
        try:
            tree = ast.parse(clean_expr, mode="eval").body
            result = _safe_eval(tree)
            return {"expression": clean_expr, "result": result, "status": "success"}
        except ZeroDivisionError:
            return {"expression": clean_expr, "error": "Division by zero", "status": "error"}
        except Exception as e:
            return {
                "expression": clean_expr,
                "error": f"Evaluation error: {str(e)}",
                "status": "error",
            }

    @mcp.tool(
        name="fetch_webpage",
        description="Fetch a remote web page or API and extract its title and clean readable text content.",
    )
    async def fetch_webpage(url: str, max_chars: int = 4000) -> Dict[str, Any]:
        """Fetch remote URL content with timeout and sanitization."""
        if not (url.startswith("http://") or url.startswith("https://")):
            return {"error": "Invalid URL scheme. Must begin with http:// or https://", "url": url}

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {"User-Agent": "Remote-MCP-Server/0.1.0"}
                resp = await client.get(url, headers=headers)
                status_code = resp.status_code
                content_type = resp.headers.get("content-type", "")

                if "json" in content_type:
                    return {
                        "url": str(resp.url),
                        "status_code": status_code,
                        "content_type": content_type,
                        "data": resp.json(),
                    }

                raw_html = resp.text
                # Extract title
                title_match = re.search(r"<title>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
                title = title_match.group(1).strip() if title_match else "No title"

                # Strip script and style tags
                clean_text = re.sub(r"<(script|style).*?</\1>", "", raw_html, flags=re.IGNORECASE | re.DOTALL)
                # Strip remaining HTML tags
                clean_text = re.sub(r"<[^>]+>", " ", clean_text)
                # Normalize whitespace
                clean_text = re.sub(r"\s+", " ", clean_text).strip()

                truncated = len(clean_text) > max_chars
                final_text = clean_text[:max_chars] + ("..." if truncated else "")

                return {
                    "url": str(resp.url),
                    "status_code": status_code,
                    "title": title,
                    "content": final_text,
                    "truncated": truncated,
                    "total_length": len(clean_text),
                }
        except httpx.TimeoutException:
            return {"error": "Request timed out after 10 seconds", "url": url}
        except Exception as e:
            return {"error": f"Failed to fetch URL: {str(e)}", "url": url}

    @mcp.tool(
        name="query_json",
        description="Extract a value from a JSON string using dot notation path (e.g., 'users[0].name' or 'status.code').",
    )
    def query_json(json_string: str, query_path: str = "") -> Dict[str, Any]:
        """Navigate and extract nested data from JSON."""
        try:
            data = json.loads(json_string)
        except Exception as e:
            return {"error": f"Invalid JSON input: {str(e)}"}

        if not query_path:
            return {"result": data, "path": ""}

        current = data
        parts = query_path.split(".")
        try:
            for part in parts:
                if "[" in part and part.endswith("]"):
                    prop, idx = part[:-1].split("[", 1)
                    if prop:
                        current = current[prop]
                    current = current[int(idx)]
                else:
                    current = current[part]
            return {"query_path": query_path, "result": current, "status": "success"}
        except Exception as e:
            return {"query_path": query_path, "error": f"Path not found: {str(e)}", "status": "not_found"}
