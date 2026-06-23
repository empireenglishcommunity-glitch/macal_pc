"""
Persistent Memory System — Agent remembers across sessions.

Stores facts, preferences, corrections, and task history in SQLite.
Injected into LLM prompts to give the agent context about the user.

Categories:
- preference: User preferences (naming conventions, folder locations)
- fact: Known facts (project paths, file locations, contacts)
- correction: Past mistakes and their corrections
- history: Recent task summaries
"""
import sqlite3
import time
from pathlib import Path
from typing import Optional


class AgentMemory:
    """Persistent memory store for the AI agent."""

    def __init__(self, db_path: str = ""):
        if not db_path:
            db_path = str(Path.home() / ".macal_agent_memory.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS memories ("
            "id INTEGER PRIMARY KEY, "
            "category TEXT NOT NULL, "
            "key TEXT NOT NULL, "
            "value TEXT NOT NULL, "
            "created_at REAL, "
            "accessed_at REAL, "
            "access_count INTEGER DEFAULT 0, "
            "UNIQUE(category, key))"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS task_history ("
            "id INTEGER PRIMARY KEY, "
            "timestamp REAL, "
            "instruction TEXT, "
            "status TEXT, "
            "tools_used TEXT, "
            "duration_ms INTEGER)"
        )
        conn.commit()
        conn.close()

    def remember(self, category: str, key: str, value: str):
        """Store or update a memory."""
        conn = sqlite3.connect(self.db_path)
        now = time.time()
        conn.execute(
            "INSERT INTO memories (category, key, value, created_at, accessed_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(category, key) DO UPDATE SET value=?, accessed_at=?",
            (category, key, value, now, now, value, now)
        )
        conn.commit()
        conn.close()

    def recall(self, category: str, key: str) -> Optional[str]:
        """Retrieve a specific memory."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT value FROM memories WHERE category=? AND key=?",
            (category, key)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE memories SET accessed_at=?, access_count=access_count+1 "
                "WHERE category=? AND key=?",
                (time.time(), category, key)
            )
            conn.commit()
        conn.close()
        return row[0] if row else None

    def recall_category(self, category: str, limit: int = 20) -> list:
        """Get all memories in a category."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT key, value FROM memories WHERE category=? "
            "ORDER BY accessed_at DESC LIMIT ?",
            (category, limit)
        ).fetchall()
        conn.close()
        return [{"key": r[0], "value": r[1]} for r in rows]

    def search(self, query: str, limit: int = 10) -> list:
        """Search memories by key or value."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT category, key, value FROM memories "
            "WHERE key LIKE ? OR value LIKE ? "
            "ORDER BY accessed_at DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()
        conn.close()
        return [{"category": r[0], "key": r[1], "value": r[2]} for r in rows]

    def forget(self, category: str, key: str):
        """Delete a specific memory."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "DELETE FROM memories WHERE category=? AND key=?",
            (category, key)
        )
        conn.commit()
        conn.close()

    def log_task(self, instruction: str, status: str, tools_used: str, duration_ms: int):
        """Log a completed task to history."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO task_history (timestamp, instruction, status, tools_used, duration_ms) "
            "VALUES (?, ?, ?, ?, ?)",
            (time.time(), instruction, status, tools_used, duration_ms)
        )
        # Keep only last 100 tasks
        conn.execute(
            "DELETE FROM task_history WHERE id NOT IN "
            "(SELECT id FROM task_history ORDER BY timestamp DESC LIMIT 100)"
        )
        conn.commit()
        conn.close()

    def get_recent_tasks(self, limit: int = 5) -> list:
        """Get recent task history."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT instruction, status, tools_used, duration_ms FROM task_history "
            "ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [{"instruction": r[0], "status": r[1], "tools": r[2], "ms": r[3]} for r in rows]

    def get_context_for_prompt(self) -> str:
        """Generate context string to inject into LLM prompts."""
        parts = []

        # User preferences
        prefs = self.recall_category("preference", limit=10)
        if prefs:
            parts.append("USER PREFERENCES:")
            for p in prefs:
                parts.append(f"  - {p['key']}: {p['value']}")

        # Known facts
        facts = self.recall_category("fact", limit=10)
        if facts:
            parts.append("KNOWN FACTS:")
            for f in facts:
                parts.append(f"  - {f['key']}: {f['value']}")

        # Recent corrections
        corrections = self.recall_category("correction", limit=5)
        if corrections:
            parts.append("PAST CORRECTIONS (avoid these mistakes):")
            for c in corrections:
                parts.append(f"  - {c['key']}: {c['value']}")

        # Recent tasks
        recent = self.get_recent_tasks(3)
        if recent:
            parts.append("RECENT TASKS:")
            for t in recent:
                parts.append(f"  - [{t['status']}] {t['instruction']}")

        return "\n".join(parts) if parts else ""

    def get_stats(self) -> dict:
        """Get memory statistics."""
        conn = sqlite3.connect(self.db_path)
        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        categories = conn.execute(
            "SELECT category, COUNT(*) FROM memories GROUP BY category"
        ).fetchall()
        tasks = conn.execute("SELECT COUNT(*) FROM task_history").fetchone()[0]
        conn.close()
        return {
            "total_memories": total,
            "categories": {r[0]: r[1] for r in categories},
            "tasks_logged": tasks,
        }
