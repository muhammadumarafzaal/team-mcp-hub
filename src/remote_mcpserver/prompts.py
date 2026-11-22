from __future__ import annotations

from fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register MCP prompt templates on the FastMCP instance."""

    @mcp.prompt(
        "daily_standup",
        description="Generate a clean, structured daily standup update for the team.",
    )
    def daily_standup(
        yesterday: str = "",
        today: str = "",
        blockers: str = "None",
    ) -> str:
        return f"""Please format the following notes into a concise, professional daily standup message for Slack/Discord:

- **Completed Yesterday:** {yesterday or 'General sprint progress'}
- **Planned for Today:** {today or 'Working on prioritized tasks'}
- **Current Blockers:** {blockers}

Include bullet points and clear highlights."""

    @mcp.prompt(
        "code_review",
        description="Template for conducting a thorough, constructive code review.",
    )
    def code_review(code_or_diff: str, focus_area: str = "general") -> str:
        return f"""Perform an in-depth senior engineering code review on the following changes.
Focus area requested: {focus_area}

Evaluate:
1. Correctness and edge cases.
2. Performance and resource utilization.
3. Security considerations (sanitization, authentication, authorization).
4. Code readability and adherence to team conventions.

Code / Diff to review:
```
{code_or_diff}
```
"""

    @mcp.prompt(
        "architecture_decision_record",
        description="Template for creating an Architecture Decision Record (ADR).",
    )
    def architecture_decision_record(title: str, context: str, decision: str) -> str:
        return f"""Create an Architecture Decision Record (ADR) using the standard MADR format:

# ADR: {title}

## Context and Problem Statement
{context}

## Decision Outcome
{decision}

Please generate:
- Status (Proposed / Accepted)
- Considered Options
- Pros and Cons of each option
- Consequences (positive and negative)
"""
