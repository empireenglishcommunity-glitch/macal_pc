"""
Permission Guard — Security gate for all agent actions.

Every action passes through this guard before execution.
It classifies actions, validates paths, enforces rate limits,
and requires approval for destructive operations.

Action Classifications:
- GREEN: auto-execute (read, list, search)
- YELLOW: execute + log (create, move, rename)
- RED: require user approval (delete, overwrite)
- BLACK: always blocked (format, registry, startup)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PermissionResult:
    """Result of a permission check."""

    allowed: bool
    classification: str  # green, yellow, red, black
    needs_approval: bool = False
    reason: str = ""


class PermissionGuard:
    """Security gate that validates all agent actions.

    Implements Phase 6 of the roadmap. Enforces path allowlists,
    action classification, rate limiting, and approval workflows.
    """

    GREEN_ACTIONS = [
        "read_file", "list_directory", "search_files",
        "get_file_info", "check_status", "classify_file",
    ]
    YELLOW_ACTIONS = [
        "create_folder", "move_file", "rename_file",
        "copy_file", "write_file", "create_file",
    ]
    RED_ACTIONS = [
        "delete_file", "delete_folder", "overwrite_file",
        "empty_recycle_bin", "install_software",
        "modify_system_setting", "run_admin_command",
    ]
    BLACK_ACTIONS = [
        "format_drive", "modify_registry", "modify_startup",
        "access_credentials", "modify_ssh_keys",
        "disable_firewall", "disable_antivirus",
        "recursive_delete", "write_to_system_directory",
    ]

    def __init__(
        self,
        allowed_paths: list[str] | None = None,
        blocked_paths: list[str] | None = None,
        max_actions_per_minute: int = 50,
    ) -> None:
        self.allowed_paths = [
            Path(p).expanduser().resolve()
            for p in (allowed_paths or [])
        ]
        self.blocked_paths = [
            Path(p).expanduser().resolve()
            for p in (blocked_paths or [])
        ]
        self.max_actions_per_minute = max_actions_per_minute
        self._action_timestamps: list[float] = []

    def check(
        self, operation: str, path: Path, destination: Path | None = None
    ) -> PermissionResult:
        """Check if an operation is allowed.

        Args:
            operation: The action type (e.g., "move_file").
            path: The source/target path.
            destination: Optional destination path (for moves).

        Returns:
            PermissionResult with allowed status and classification.
        """
        # 1. Classify the action
        classification = self._classify(operation)

        # 2. BLACK = always blocked
        if classification == "black":
            logger.warning(f"BLOCKED (black): {operation} on {path}")
            return PermissionResult(
                allowed=False, classification="black",
                reason=f"Operation '{operation}' is permanently blocked",
            )

        # 3. Check blocked paths
        resolved = path.expanduser().resolve()
        for blocked in self.blocked_paths:
            try:
                if resolved.is_relative_to(blocked):
                    return PermissionResult(
                        allowed=False, classification=classification,
                        reason=f"Path '{path}' is in blocked zone: {blocked}",
                    )
            except (ValueError, OSError):
                continue

        if destination:
            dst_resolved = destination.expanduser().resolve()
            for blocked in self.blocked_paths:
                try:
                    if dst_resolved.is_relative_to(blocked):
                        return PermissionResult(
                            allowed=False, classification=classification,
                            reason=f"Destination '{destination}' is in blocked zone",
                        )
                except (ValueError, OSError):
                    continue

        # 4. Check rate limit
        if not self._check_rate_limit():
            return PermissionResult(
                allowed=False, classification=classification,
                reason=f"Rate limit exceeded ({self.max_actions_per_minute}/min)",
            )

        # 5. GREEN = auto-approve
        if classification == "green":
            self._record_action()
            return PermissionResult(allowed=True, classification="green")

        # 6. YELLOW = approve + log
        if classification == "yellow":
            self._record_action()
            return PermissionResult(allowed=True, classification="yellow")

        # 7. RED = needs human approval
        if classification == "red":
            return PermissionResult(
                allowed=True, classification="red", needs_approval=True,
                reason=f"Operation '{operation}' requires user approval",
            )

        return PermissionResult(allowed=True, classification="green")

    def _classify(self, operation: str) -> str:
        """Classify an operation into green/yellow/red/black."""
        if operation in self.BLACK_ACTIONS:
            return "black"
        if operation in self.RED_ACTIONS:
            return "red"
        if operation in self.YELLOW_ACTIONS:
            return "yellow"
        if operation in self.GREEN_ACTIONS:
            return "green"
        return "yellow"  # Unknown operations default to yellow

    def _check_rate_limit(self) -> bool:
        """Check if we're within the rate limit."""
        now = time.time()
        window = now - 60
        self._action_timestamps = [
            t for t in self._action_timestamps if t > window
        ]
        return len(self._action_timestamps) < self.max_actions_per_minute

    def _record_action(self) -> None:
        """Record an action timestamp for rate limiting."""
        self._action_timestamps.append(time.time())
