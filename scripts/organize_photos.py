"""
iPhone Photo Organizer — Sorts photos/videos by type and date.
No AI needed — uses file extension + modification date.
Fast: processes 1000+ files in seconds.

Usage:
    python scripts/organize_photos.py

Structure created:
    C:\Iphone Photos Backup\
        Photos\2026-04\
        Photos\2026-05\
        Videos\2026-04\
        Screenshots\2026-04\
"""
import os
import shutil
import sqlite3
import time
from pathlib import Path
from datetime import datetime

# Configuration
SOURCE_DIR = Path("C:/Iphone Photos Backup")
ORGANIZE_IN_PLACE = True  # Organize within the same folder (not move elsewhere)

# File type categories
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".heic", ".heif", ".dng", ".raw", ".cr2"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".3gp"}
SCREENSHOT_EXTENSIONS = {".png"}  # iPhone screenshots are PNG
LIVE_PHOTO_EXTENSIONS = {".aae"}

# Database for tracking (enables undo)
DB_PATH = SOURCE_DIR / ".organize_log.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS moves ("
        "id INTEGER PRIMARY KEY, "
        "timestamp TEXT DEFAULT CURRENT_TIMESTAMP, "
        "original_path TEXT, "
        "new_path TEXT, "
        "undone INTEGER DEFAULT 0)"
    )
    conn.commit()
    return conn


def get_category(ext):
    """Determine category from file extension."""
    ext = ext.lower()
    if ext in PHOTO_EXTENSIONS:
        return "Photos"
    elif ext in VIDEO_EXTENSIONS:
        return "Videos"
    elif ext in SCREENSHOT_EXTENSIONS:
        return "Screenshots"
    elif ext in LIVE_PHOTO_EXTENSIONS:
        return "LivePhoto-Data"
    else:
        return "Other"


def get_date_folder(filepath):
    """Get YYYY-MM from file modification date."""
    try:
        mtime = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime("%Y-%m")
    except Exception:
        return "Unknown-Date"


def organize():
    """Main organization logic."""
    if not SOURCE_DIR.exists():
        print("ERROR: Source directory not found: " + str(SOURCE_DIR))
        return

    conn = init_db()
    files = [f for f in SOURCE_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]

    if not files:
        print("No files to organize.")
        return

    print("Found " + str(len(files)) + " files to organize...")
    print("Source: " + str(SOURCE_DIR))
    print("")

    stats = {}
    moved = 0
    skipped = 0

    for f in files:
        ext = f.suffix.lower()
        category = get_category(ext)
        date_folder = get_date_folder(f)

        # Build destination path
        dest_dir = SOURCE_DIR / category / date_folder
        dest_path = dest_dir / f.name

        # Skip if already in correct location
        if f.parent == dest_dir:
            skipped += 1
            continue

        # Handle duplicates
        if dest_path.exists():
            stem = f.stem
            dest_path = dest_dir / (stem + "_" + str(int(time.time())) + f.suffix)

        # Create directory and move
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Log before move
        conn.execute(
            "INSERT INTO moves (original_path, new_path) VALUES (?, ?)",
            (str(f), str(dest_path))
        )

        shutil.move(str(f), str(dest_path))
        moved += 1

        # Track stats
        key = category + "/" + date_folder
        stats[key] = stats.get(key, 0) + 1

    conn.commit()
    conn.close()

    # Print summary
    print("=" * 50)
    print("DONE! Organized " + str(moved) + " files (" + str(skipped) + " already organized)")
    print("=" * 50)
    print("")
    for key in sorted(stats.keys()):
        print("  " + key + ": " + str(stats[key]) + " files")
    print("")
    print("Undo available: python scripts/organize_photos.py undo")


def undo(count=None):
    """Undo photo organization."""
    if not DB_PATH.exists():
        print("No organization history found.")
        return

    conn = sqlite3.connect(DB_PATH)
    if count:
        ops = conn.execute(
            "SELECT id, original_path, new_path FROM moves WHERE undone=0 ORDER BY id DESC LIMIT ?",
            (count,)
        ).fetchall()
    else:
        ops = conn.execute(
            "SELECT id, original_path, new_path FROM moves WHERE undone=0 ORDER BY id DESC"
        ).fetchall()

    if not ops:
        print("Nothing to undo.")
        return

    print("Undoing " + str(len(ops)) + " moves...")
    undone = 0
    for op_id, orig, new in ops:
        if Path(new).exists():
            Path(orig).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(new, orig)
            conn.execute("UPDATE moves SET undone=1 WHERE id=?", (op_id,))
            undone += 1

    conn.commit()
    conn.close()
    print("Undone: " + str(undone) + " files moved back.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "undo":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else None
        undo(count)
    else:
        organize()
