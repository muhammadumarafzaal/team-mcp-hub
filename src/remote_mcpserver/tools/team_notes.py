from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


class TeamNotesStore:
    """Simple persistent JSON storage for team notes and announcements."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.file_path = data_dir / "team_notes.json"
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                self.file_path.write_text("{}", encoding="utf-8")
        except Exception as e:
            logger.error("Failed to initialize notes storage: %s", e)

    def _read_all(self) -> Dict[str, Dict[str, Any]]:
        try:
            if not self.file_path.exists():
                return {}
            content = self.file_path.read_text(encoding="utf-8").strip()
            return json.loads(content) if content else {}
        except Exception as e:
            logger.error("Error reading notes: %s", e)
            return {}

    def _write_all(self, data: Dict[str, Dict[str, Any]]) -> None:
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error("Error saving notes: %s", e)

    def save(
        self,
        title: str,
        content: str,
        author: str = "Anonymous",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        data = self._read_all()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        is_update = title in data

        note = {
            "title": title,
            "content": content,
            "author": author,
            "tags": tags or [],
            "created_at": data[title]["created_at"] if is_update else now,
            "updated_at": now,
        }
        data[title] = note
        self._write_all(data)
        return {
            "success": True,
            "action": "updated" if is_update else "created",
            "note": note,
        }

    def list(
        self, tag: Optional[str] = None, author: Optional[str] = None
    ) -> Dict[str, Any]:
        data = self._read_all()
        results: List[Dict[str, Any]] = []
        for note in data.values():
            if tag and tag.lower() not in [t.lower() for t in note.get("tags", [])]:
                continue
            if author and author.lower() != note.get("author", "").lower():
                continue
            # Return preview without massive content in list view
            results.append({
                "title": note["title"],
                "author": note["author"],
                "tags": note["tags"],
                "created_at": note["created_at"],
                "updated_at": note["updated_at"],
                "preview": note["content"][:100] + ("..." if len(note["content"]) > 100 else ""),
            })
        return {"count": len(results), "notes": results}

    def get(self, title: str) -> Optional[Dict[str, Any]]:
        data = self._read_all()
        return data.get(title)

    def delete(self, title: str) -> bool:
        data = self._read_all()
        if title in data:
            del data[title]
            self._write_all(data)
            return True
        return False

    def search(self, query: str) -> List[Dict[str, Any]]:
        data = self._read_all()
        query_lower = query.lower()
        matches: List[Dict[str, Any]] = []
        for note in data.values():
            if (
                query_lower in note["title"].lower()
                or query_lower in note["content"].lower()
                or any(query_lower in t.lower() for t in note.get("tags", []))
            ):
                matches.append(note)
        return matches


def register_team_notes_tools(mcp: FastMCP, data_dir: Path) -> None:
    """Register persistent team collaboration notes tools."""
    store = TeamNotesStore(data_dir)

    @mcp.tool(
        name="save_team_note",
        description="Save or update a shared note on the team server. Supports markdown content, author name, and tags.",
    )
    def save_team_note(
        title: str,
        content: str,
        author: str = "Anonymous",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Save a shared note, documentation snippet, or announcement for the team."""
        return store.save(title=title, content=content, author=author, tags=tags)

    @mcp.tool(
        name="list_team_notes",
        description="List all shared team notes. Can filter by tag or author.",
    )
    def list_team_notes(
        tag: Optional[str] = None, author: Optional[str] = None
    ) -> Dict[str, Any]:
        """List team notes with summary metadata and previews."""
        return store.list(tag=tag, author=author)

    @mcp.tool(
        name="get_team_note",
        description="Retrieve the full content and metadata of a team note by exact title.",
    )
    def get_team_note(title: str) -> Dict[str, Any]:
        """Get full details of a specific team note."""
        note = store.get(title)
        if not note:
            return {"found": False, "error": f"Note '{title}' not found."}
        return {"found": True, "note": note}

    @mcp.tool(
        name="search_team_notes",
        description="Search team notes by keyword across title, content, and tags.",
    )
    def search_team_notes(query: str) -> Dict[str, Any]:
        """Search notes by keyword."""
        matches = store.search(query)
        return {"query": query, "count": len(matches), "results": matches}

    @mcp.tool(
        name="delete_team_note",
        description="Delete a team note by exact title.",
    )
    def delete_team_note(title: str) -> Dict[str, Any]:
        """Delete a note from the shared team board."""
        success = store.delete(title)
        return {
            "title": title,
            "deleted": success,
            "message": "Note deleted successfully." if success else "Note not found.",
        }
