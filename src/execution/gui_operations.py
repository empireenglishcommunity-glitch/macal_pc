"""
GUI Operations — Windows desktop automation via pywinauto + pyautogui.

Provides reliable methods to:
- Open applications
- Find windows by title
- Type text into the active window (via clipboard paste)
- Click at positions or on UI elements
- Send keyboard shortcuts
- List open windows

Uses the "Desktop find + clipboard paste" pattern which works
reliably with Windows 11's modern apps (UWP, WinUI 3).
"""

from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass

import pyautogui

logger = logging.getLogger(__name__)

# Safety: pyautogui failsafe (move mouse to corner = abort)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


@dataclass
class GUIOpResult:
    """Result of a GUI operation."""

    success: bool
    operation: str
    details: str = ""
    error: str = ""


class GUIOperations:
    """Windows desktop automation using pywinauto + pyautogui.

    Designed for reliability on Windows 11 with modern apps.
    Uses clipboard-paste for text input (works everywhere).
    """

    async def open_application(self, app_name: str) -> GUIOpResult:
        """Open a Windows application by name.

        Supports: notepad, explorer, calc, browser, cmd, powershell,
        or any executable name/path.
        """
        # Map common names to executables
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "terminal": "cmd.exe",
            "powershell": "powershell.exe",
            "browser": "start https://",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "settings": "ms-settings:",
            "paint": "mspaint.exe",
            "wordpad": "wordpad.exe",
        }

        executable = app_map.get(app_name.lower(), app_name)

        try:
            if executable.startswith("ms-settings:") or executable.startswith("start "):
                subprocess.Popen(f"start {executable}", shell=True)
            else:
                subprocess.Popen(executable, shell=True)

            time.sleep(3)  # Wait for app to open
            logger.info(f"Opened application: {app_name} ({executable})")
            return GUIOpResult(
                success=True, operation="open_application",
                details=f"Opened {app_name}",
            )
        except Exception as e:
            return GUIOpResult(
                success=False, operation="open_application",
                error=f"Failed to open {app_name}: {e}",
            )

    async def type_text(self, text: str, window_title: str = "") -> GUIOpResult:
        """Type text into a window using clipboard paste (most reliable).

        Args:
            text: The text to type.
            window_title: Optional window to focus first.
        """
        try:
            # Focus the target window if specified
            if window_title:
                focused = await self._focus_window(window_title)
                if not focused:
                    return GUIOpResult(
                        success=False, operation="type_text",
                        error=f"Could not find window: {window_title}",
                    )
                time.sleep(0.5)

            # Use clipboard paste (works with all apps)
            subprocess.run(
                ["powershell", "-Command", f'Set-Clipboard -Value "{text}"'],
                capture_output=True, timeout=5,
            )
            time.sleep(0.3)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.3)

            logger.info(f"Typed text ({len(text)} chars) into {window_title or 'active window'}")
            return GUIOpResult(
                success=True, operation="type_text",
                details=f"Typed {len(text)} characters into {window_title or 'active window'}",
            )
        except Exception as e:
            return GUIOpResult(
                success=False, operation="type_text",
                error=f"Failed to type text: {e}",
            )

    async def press_keys(self, keys: str) -> GUIOpResult:
        """Send a keyboard shortcut or key press.

        Args:
            keys: Key combination like "ctrl+s", "alt+f4", "enter", "tab"
        """
        try:
            parts = [k.strip() for k in keys.lower().split("+")]

            if len(parts) == 1:
                pyautogui.press(parts[0])
            else:
                pyautogui.hotkey(*parts)

            time.sleep(0.3)
            logger.info(f"Pressed keys: {keys}")
            return GUIOpResult(
                success=True, operation="press_keys",
                details=f"Pressed {keys}",
            )
        except Exception as e:
            return GUIOpResult(
                success=False, operation="press_keys",
                error=f"Failed to press keys: {e}",
            )

    async def list_windows(self) -> GUIOpResult:
        """List all open windows with their titles."""
        try:
            from pywinauto import Desktop
            d = Desktop(backend="uia")
            windows = d.windows()
            titles = [w.window_text() for w in windows if w.window_text().strip()]
            # Filter out empty and system windows
            titles = [t for t in titles if t and t != "Taskbar" and len(t) > 1]

            logger.info(f"Listed {len(titles)} open windows")
            return GUIOpResult(
                success=True, operation="list_windows",
                details="; ".join(titles[:15]),  # Cap at 15
            )
        except Exception as e:
            return GUIOpResult(
                success=False, operation="list_windows",
                error=f"Failed to list windows: {e}",
            )

    async def focus_window(self, window_title: str) -> GUIOpResult:
        """Bring a window to the foreground by its title (partial match)."""
        focused = await self._focus_window(window_title)
        if focused:
            return GUIOpResult(
                success=True, operation="focus_window",
                details=f"Focused window: {window_title}",
            )
        return GUIOpResult(
            success=False, operation="focus_window",
            error=f"Window not found: {window_title}",
        )

    async def _focus_window(self, title: str) -> bool:
        """Internal: find and focus a window by title (partial match)."""
        try:
            from pywinauto import Desktop
            d = Desktop(backend="uia")
            windows = d.windows()
            matches = [w for w in windows if title.lower() in w.window_text().lower()]

            if not matches:
                return False

            matches[0].set_focus()
            time.sleep(0.5)
            return True
        except Exception:
            return False
