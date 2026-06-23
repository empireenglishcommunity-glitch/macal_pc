"""
Separate My Photos — Uses EXIF metadata to identify YOUR photos vs received ones.

Photos taken by YOUR iPhone have EXIF data with Make=Apple, Model=iPhone.
Downloaded, WhatsApp, or received images typically have no EXIF or different camera info.

Creates:
    C:\Iphone Photos Backup\
        My-Photos\YYYY-MM\     (taken by your iPhone camera)
        Received\YYYY-MM\      (WhatsApp, downloaded, no EXIF)
        Screenshots\YYYY-MM\   (PNG files)
        Videos\YYYY-MM\        (MP4, MOV files)

Usage:
    python scripts/separate_my_photos.py

Undo:
    python scripts/separate_my_photos.py undo
"""
import os
import shutil
import sqlite3
import time
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
    from PIL import Image
    from PIL.ExifTags import TAGS

# Configuration
SOURCE_DIR = Path("C:/Iphone Photos Backup")
DB_PATH = SOURCE_DIR / ".separate_log.db"

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".heic", ".heif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".3gp"}
SCREENSHOT_EXTENSIONS = {".png"}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS moves ("
        "id INTEGER PRIMARY KEY, "
        "timestamp TEXT DEFAULT CURRENT_TIMESTAMP, "
        "original_path TEXT, "
        "new_path TEXT, "
        "category TEXT, "
        "undone INTEGER DEFAULT 0)"
    )
    conn.commit()
    return conn


def get_exif_camera(filepath):
    """Read EXIF data and return camera make/model."""
    try:
        img = Image.open(filepath)
        exif_data = img._getexif()
        img.close()
        if not exif_data:
            return None, None
        make = ""
        model = ""
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == "Make":
                make = str(value).strip()
            elif tag_name == "Model":
                model = str(value).strip()
        return make, model
    except Exception:
        return None, None


def is_my_photo(filepath):
    """Determine if a photo was taken by the user's iPhone."""
    make, model = get_exif_camera(filepath)
    if make and "apple" in make.lower():
        return True
    if model and "iphone" in model.lower():
        return True
    return False


def get_date_folder(filepath):
    """Get YYYY-MM from file modification date."""
    try:
        mtime = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime("%Y-%m")
    except Exception:
        return "Unknown-Date"


def categorize_file(filepath):
    """Determine category for a file."""
    ext = filepath.suffix.lower()

    if ext in VIDEO_EXTENSIONS:
        return "Videos"
    elif ext in SCREENSHOT_EXTENSIONS:
        return "Screenshots"
    elif ext in PHOTO_EXTENSIONS:
        if is_my_photo(filepath):
            return "My-Photos"
        else:
            return "Received"
    else:
        return "Other"


def organize():
    """Main separation logic."""
    if not SOURCE_DIR.exists():
        print("ERROR: Source directory not found: " + str(SOURCE_DIR))
        return

    conn = init_db()

    # Collect all files (including from subdirectories created by previous organize)
    files = []
    for root, dirs, filenames in os.walk(SOURCE_DIR):
        # Skip hidden/system dirs
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in filenames:
            if fname.startswith("."):
                continue
            fpath = Path(root) / fname
            if fpath.is_file():
                files.append(fpath)

    if not files:
        print("No files to organize.")
        return

    print("Analyzing " + str(len(files)) + " files...")
    print("Reading EXIF data to identify YOUR photos...")
    print("")

    stats = {}
    moved = 0
    skipped = 0
    errors = 0

    for i, f in enumerate(files, 1):
        if i % 100 == 0:
            print("  Progress: " + str(i) + "/" + str(len(files)) + "...")

        try:
            category = categorize_file(f)
            date_folder = get_date_folder(f)

            # Build destination
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

            conn.execute(
                "INSERT INTO moves (original_path, new_path, category) VALUES (?, ?, ?)",
                (str(f), str(dest_path), category)
            )

            shutil.move(str(f), str(dest_path))
            moved += 1

            key = category
            stats[key] = stats.get(key, 0) + 1

        except Exception as e:
            errors += 1
            if errors <= 5:
                print("  Error on " + f.name + ": " + str(e))

    conn.commit()
    conn.close()

    # Clean empty directories
    for root, dirs, filenames in os.walk(SOURCE_DIR, topdown=False):
        for d in dirs:
            dir_path = Path(root) / d
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
            except Exception:
                pass

    # Print summary
    print("")
    print("=" * 50)
    print("DONE! Separated " + str(moved) + " files")
    print("  Skipped (already organized): " + str(skipped))
    print("  Errors: " + str(errors))
    print("=" * 50)
    print("")
    for key in sorted(stats.keys()):
        print("  " + key + ": " + str(stats[key]) + " files")
    print("")
    print("Your photos are in: " + str(SOURCE_DIR / "My-Photos"))
    print("Received/downloaded in: " + str(SOURCE_DIR / "Received"))
    print("")
    print("Undo: python scripts/separate_my_photos.py undo")


def undo(count=None):
    """Undo separation."""
    if not DB_PATH.exists():
        print("No history found.")
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
