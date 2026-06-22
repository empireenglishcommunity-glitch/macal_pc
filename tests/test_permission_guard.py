"""
Tests for the Permission Guard security module.

These tests verify that the security layer correctly:
- Blocks black-listed operations
- Requires approval for red operations
- Auto-approves green operations
- Enforces path restrictions
- Respects rate limits
"""

from pathlib import Path

from src.security.permission_guard import PermissionGuard


def get_guard() -> PermissionGuard:
    """Create a PermissionGuard with test configuration."""
    return PermissionGuard(
        allowed_paths=["~/Organized", "~/AgentWork", "~/Downloads"],
        blocked_paths=["C:/Windows", "C:/Program Files", "~/.ssh"],
        max_actions_per_minute=50,
    )


def test_green_action_auto_approved():
    """Green actions (read, list) should be auto-approved."""
    guard = get_guard()
    result = guard.check("read_file", Path("~/Documents/test.txt"))
    assert result.allowed is True
    assert result.classification == "green"
    assert result.needs_approval is False


def test_yellow_action_allowed_with_log():
    """Yellow actions (create, move) should be allowed in valid paths."""
    guard = get_guard()
    result = guard.check("create_folder", Path("~/Organized/NewFolder"))
    assert result.allowed is True
    assert result.classification == "yellow"
    assert result.needs_approval is False


def test_red_action_requires_approval():
    """Red actions (delete) should require user approval."""
    guard = get_guard()
    result = guard.check("delete_file", Path("~/Downloads/old.txt"))
    assert result.allowed is True
    assert result.classification == "red"
    assert result.needs_approval is True


def test_black_action_always_blocked():
    """Black actions (format, registry) should ALWAYS be blocked."""
    guard = get_guard()
    result = guard.check("format_drive", Path("C:/"))
    assert result.allowed is False
    assert result.classification == "black"


def test_blocked_path_rejected():
    """Operations targeting blocked paths should be rejected."""
    guard = get_guard()
    result = guard.check("create_folder", Path("C:/Windows/test"))
    assert result.allowed is False
    assert "blocked zone" in result.reason


def test_blocked_destination_rejected():
    """Move operations with blocked destinations should be rejected."""
    guard = get_guard()
    result = guard.check(
        "move_file",
        Path("~/Downloads/file.txt"),
        destination=Path("C:/Windows/file.txt"),
    )
    assert result.allowed is False


def test_rate_limit_enforced():
    """Rate limiting should block after max actions per minute."""
    guard = PermissionGuard(max_actions_per_minute=5)
    for _ in range(5):
        result = guard.check("list_directory", Path("~/Downloads"))
        assert result.allowed is True

    result = guard.check("list_directory", Path("~/Downloads"))
    assert result.allowed is False
    assert "rate limit" in result.reason.lower()


def test_unknown_operation_defaults_yellow():
    """Unknown operations should default to yellow classification."""
    guard = get_guard()
    result = guard.check("some_unknown_action", Path("~/Organized/test"))
    assert result.classification == "yellow"
