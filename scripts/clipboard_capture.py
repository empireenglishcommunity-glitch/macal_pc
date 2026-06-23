"""
Clipboard Quick-Capture — Save clipboard to notes with one hotkey.

Runs in the background. When you press Ctrl+Shift+S, it:
1. Reads whatever is on the clipboard
2. Appends it to ~/Documents/Notes/captures.md with a timestamp
3. Prints confirmation

Usage:
    python scripts/clipboard_capture.py

Press Ctrl+C to stop.
"""
import time
import sys
from pathlib import Path
from datetime import datetime

try:
    import pyperclip
except ImportError:
    print("Installing pyperclip...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pyperclip", "-q"])
    import pyperclip

try:
    import keyboard
except ImportError:
    print("Installing keyboard...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "keyboard", "-q"])
    import keyboard


NOTES_DIR = Path.home() / "Documents" / "Notes"
CAPTURES_FILE = NOTES_DIR / "captures.md"


def capture_clipboard():
    """Grab clipboard and save to captures file."""
    try:
        content = pyperclip.paste()
        if not content or not content.strip():
            print("  [Clipboard empty - nothing captured]")
            return

        # Ensure notes directory exists
        NOTES_DIR.mkdir(parents=True, exist_ok=True)

        # Format the entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n---\n**Captured: {timestamp}**\n\n{content.strip()}\n"

        # Append to file
        with open(CAPTURES_FILE, "a", encoding="utf-8") as f:
            f.write(entry)

        # Show confirmation
        preview = content.strip()[:60]
        print(f"  Captured: \"{preview}{'...' if len(content.strip()) > 60 else ''}\"")
        print(f"  Saved to: {CAPTURES_FILE}")

    except Exception as e:
        print(f"  Error: {e}")


def main():
    print("=" * 50)
    print("  MACAL Clipboard Capture")
    print("  Hotkey: Ctrl+Shift+S")
    print("  Saves to: ~/Documents/Notes/captures.md")
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    keyboard.add_hotkey("ctrl+shift+s", capture_clipboard)

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\n  Clipboard capture stopped.")


if __name__ == "__main__":
    main()
