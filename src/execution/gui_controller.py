"""
GUI Controller — Unified interface for Windows desktop automation.

Routes GUI actions to the best available backend:
- agent-desktop (fast, accessibility-tree based)
- pywinauto (battle-tested, reliable)
- UFO3 (most capable, AI-native multi-app)
- AutoHotkey (fastest execution, macros)

Phase 3 implementation. This is the scaffolding.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GUIBackend(Enum):
    """Available GUI automation backends."""

    AGENT_DESKTOP = "agent_desktop"
    PYWINAUTO = "pywinauto"
    UFO3 = "ufo3"
    AUTOHOTKEY = "ahk"


@dataclass
class GUIAction:
    """A single GUI action to execute."""

    action_type: str  # click, type, scroll, hotkey, open_app, wait
    target: str = ""  # Element reference (@e1) or app name
    value: str = ""  # Text to type, key combo, scroll direction
    app: str = ""  # Application name/window title


@dataclass
class GUIResult:
    """Result of a GUI action."""

    success: bool
    action: GUIAction
    backend_used: str = ""
    error: str = ""
    screenshot_path: str = ""  # Captured on failure (if configured)


class GUIController:
    """Unified GUI control — routes to the best backend per action.

    Implements Phase 3 of the roadmap. Provides a single interface
    that abstracts over multiple automation backends, choosing the
    fastest and most reliable one for each action type.
    """

    def __init__(self, default_backend: GUIBackend = GUIBackend.AGENT_DESKTOP) -> None:
        self.default_backend = default_backend
        # TODO Phase 3: Initialize backends based on what's installed

    async def execute(self, action: GUIAction) -> GUIResult:
        """Execute a GUI action using the best available backend."""
        # TODO Phase 3: Implement backend routing and execution
        raise NotImplementedError("Phase 3: Implement GUIController.execute()")

    async def snapshot(self, app: str = "") -> dict:
        """Capture the accessibility tree of an application."""
        # TODO Phase 3: Use agent-desktop snapshot command
        raise NotImplementedError("Phase 3: Implement GUIController.snapshot()")

    def _select_backend(self, action: GUIAction) -> GUIBackend:
        """Choose the optimal backend for this action type."""
        if action.action_type == "hotkey":
            return GUIBackend.AUTOHOTKEY
        elif action.action_type in ("click", "type", "scroll"):
            return GUIBackend.AGENT_DESKTOP
        elif action.action_type == "complex_workflow":
            return GUIBackend.UFO3
        return self.default_backend
