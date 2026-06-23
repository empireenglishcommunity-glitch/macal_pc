"""
Drive W: Organizer — Sorts iCloud Photos exports by type + date.
Non-destructive: moves files within W: drive, logs everything for undo.

Creates:
    W:\Organized\
        Photos\YYYY-MM\
        Videos\YYYY-MM\
        Other\

Usage:
    python scripts/organize_drive_w.py         (organize)
    python scripts/organize_drive_w.py undo    (undo all moves)
    python scripts/organize_drive_w.py status  (show progress)
"""
import os
import shutil
import sqlite3
import time
from pathlib import Path
from datetime import datetime

# Configuration
SOURCE_DRIVE = Path("W:/")
ORGANIZE_ROOT = Path("W:/Organized")
DB_PATH = Path("W:/.organize_log.db")

# File categories
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".heic", ".heif", ".png", ".dng", ".raw", ".tiff", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".3gp", ".mkv", ".wmv"}
IGNORE_FILES = {".ds_store", "thumbs.db", "desktop.ini", ".organize_log.db"}


def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS moves ("
        "id INTEGER PRIMARY KEY, "
        "timestamp TEXT DEFAULT CURRENT_TIMESTAMP, "
        "original_path TEXT, "
        "new_path TEXT, "
        "file_type TEXT, "
        "file_size INTEGER, "
        "undone INTEGER DEFAULT 0)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS manifest ("
        "id INTEGER PRIMARY KEY, "
        "folder_path TEXT UNIQUE, "
        "file_count INTEGER, "
        "size_bytes INTEGER, "
        "date_range TEXT, "
        "status TEXT DEFAULT 'pending_review')"
    )
    conn.commit()
    return conn


def get_file_date(filepath):
    """Get date from file — tries EXIF first, falls back to modification date."""
    # Try EXIF for photos
    ext = filepath.suffix.lower()
    if ext in PHOTO_EXTENSIONS:
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            img = Image.open(str(filepath))
            exif = img._getexif()
            img.close()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, "")
                    if tag == "DateTimeOriginal":
                        dt = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                        return dt.strftime("%Y-%m")
        except Exception:
            pass

    # Fallback: file modification date
    try:
        mtime = os.path.getmtime(str(filepath))
        return datetime.fromtimestamp(mtime).strftime("%Y-%m")
    except Exception:
        return "Unknown"


def get_category(ext):
    """Determine file category."""
    ext = ext.lower()
    if ext in PHOTO_EXTENSIONS:
        return "Photos"
    elif ext in VIDEO_EXTENSIONS:
        return "Videos"
    else:
        return "Other"


def collect_all_files():
    """Recursively collect all files from W: drive (excluding Organized folder)."""
    files = []
    for root, dirs, filenames in os.walk(str(SOURCE_DRIVE)):
        # Skip the Organized output folder and hidden folders
        root_path = Path(root)
        if "Organized" in root_path.parts:
            continue
        if any(part.startswith(".") for part in root_path.parts[1:]):
            continue

        for fname in filenames:
            if fname.lower() in IGNORE_FILES:
                continue
            if fname.startswith("."):
                continue
            filepath = root_path / fname
            if filepath.is_file():
                files.append(filepath)

    return files


def organize():
    """Main organization logic."""
    conn = init_db()
    ORGANIZE_ROOT.mkdir(parents=True, exist_ok=True)

    print("Scanning W: drive for all files...")
    files = collect_all_files()
    print("Found " + str(len(files)) + " files to organize.")
    print("")

    stats = {}
    moved = 0
    skipped = 0
    errors = 0

    for i, filepath in enumerate(files, 1):
        if i % 200 == 0:
            print("  Progress: " + str(i) + "/" + str(len(files)) + " (" + str(moved) + " moved)...")

        try:
            ext = filepath.suffix.lower()
            category = get_category(ext)
            date_folder = get_file_date(filepath)

            # Build destination
            dest_dir = ORGANIZE_ROOT / category / date_folder
            dest_path = dest_dir / filepath.name

            # Skip if already in Organized
            if "Organized" in str(filepath):
                skipped += 1
                continue

            # Skip if already exists at destination
            if dest_path.exists():
                # Add timestamp to avoid collision
                stem = filepath.stem
                dest_path = dest_dir / (stem + "_" + str(int(time.time() * 1000) % 100000) + filepath.suffix)

            # Create directory
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Log the move
            file_size = filepath.stat().st_size
            conn.execute(
                "INSERT INTO moves (original_path, new_path, file_type, file_size) VALUES (?, ?, ?, ?)",
                (str(filepath), str(dest_path), category, file_size)
            )

            # Move the file
            shutil.move(str(filepath), str(dest_path))
            moved += 1

            # Track stats
            key = category + "/" + date_folder
            stats[key] = stats.get(key, 0) + 1

        except Exception as e:
            errors += 1
            if errors <= 10:
                print("  Error: " + filepath.name + " — " + str(e))

    conn.commit()

    # Generate manifest (folder inventory for review phase)
    print("\nGenerating manifest...")
    generate_manifest(conn)

    # Clean empty source directories
    print("Cleaning empty directories...")
    clean_empty_dirs(SOURCE_DRIVE)

    conn.close()

    # Print summary
    print("")
    print("=" * 60)
    print("DONE! Organized " + str(moved) + " files")
    print("  Skipped: " + str(skipped))
    print("  Errors: " + str(errors))
    print("=" * 60)
    print("")
    for key in sorted(stats.keys()):
        print("  " + key + ": " + str(stats[key]) + " files")
    print("")
    print("Organized structure at: W:\\Organized\\")
    print("Ready for review: python scripts/organize_drive_w.py status")
    print("Undo everything: python scripts/organize_drive_w.py undo")


def generate_manifest(conn):
    """Generate folder manifest for the review phase."""
    # Clear existing manifest
    conn.execute("DELETE FROM manifest")

    # Walk the organized directory
    for category_dir in ORGANIZE_ROOT.iterdir():
        if not category_dir.is_dir():
            continue
        for date_dir in category_dir.iterdir():
            if not date_dir.is_dir():
                continue
            files = list(date_dir.iterdir())
            file_count = len([f for f in files if f.is_file()])
            if file_count == 0:
                continue
            total_size = sum(f.stat().st_size for f in files if f.is_file())

            conn.execute(
                "INSERT OR REPLACE INTO manifest (folder_path, file_count, size_bytes, date_range, status) "
                "VALUES (?, ?, ?, ?, 'pending_review')",
                (str(date_dir), file_count, total_size, date_dir.name)
            )

    conn.commit()


def clean_empty_dirs(root):
    """Remove empty directories after moving files."""
    for dirpath, dirnames, filenames in os.walk(str(root), topdown=False):
        path = Path(dirpath)
        if path == root:
            continue
        if "Organized" in str(path):
            continue
        try:
            if not any(path.iterdir()):
                path.rmdir()
        except Exception:
            pass


def show_status():
    """Show organization and review status."""
    if not DB_PATH.exists():
        print("No organization data found. Run organize first.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    total_moved = conn.execute("SELECT COUNT(*) FROM moves WHERE undone=0").fetchone()[0]
    total_size = conn.execute("SELECT SUM(file_size) FROM moves WHERE undone=0").fetchone()[0] or 0

    manifest = conn.execute("SELECT folder_path, file_count, size_bytes, status FROM manifest ORDER BY folder_path").fetchall()
    conn.close()

    print("")
    print("=" * 60)
    print("  W: DRIVE ORGANIZATION STATUS")
    print("=" * 60)
    print("")
    print("  Total files organized: " + str(total_moved))
    print("  Total size: " + str(round(total_size / (1024**3), 2)) + " GB")
    print("")
    print("  Folders ready for review:")
    print("  " + "-" * 56)

    pending = 0
    approved = 0
    rejected = 0

    for folder_path, file_count, size_bytes, status in manifest:
        size_mb = round(size_bytes / (1024**2), 1)
        folder_name = Path(folder_path).relative_to(ORGANIZE_ROOT)
        icon = {"pending_review": "[ ]", "approved": "[+]", "rejected": "[x]", "skipped": "[?]"}.get(status, "[ ]")
        print("    " + icon + " " + str(folder_name) + " — " + str(file_count) + " files, " + str(size_mb) + " MB")

        if status == "pending_review":
            pending += 1
        elif status == "approved":
            approved += 1
        elif status == "rejected":
            rejected += 1

    print("")
    print("  Summary: " + str(pending) + " pending, " + str(approved) + " approved, " + str(rejected) + " rejected")
    print("")


def undo(count=None):
    """Undo organization — move files back to original locations."""
    if not DB_PATH.exists():
        print("No organization data found.")
        return

    conn = sqlite3.connect(str(DB_PATH))
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
        conn.close()
        return

    print("Undoing " + str(len(ops)) + " moves...")
    undone = 0
    for op_id, orig, new in ops:
        try:
            if Path(new).exists():
                Path(orig).parent.mkdir(parents=True, exist_ok=True)
                shutil.move(new, orig)
                conn.execute("UPDATE moves SET undone=1 WHERE id=?", (op_id,))
                undone += 1
        except Exception as e:
            print("  Error undoing: " + str(e))

    conn.commit()
    conn.close()
    print("Undone: " + str(undone) + " files moved back to original locations.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "undo":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else None
            undo(count)
        elif sys.argv[1] == "status":
            show_status()
        else:
            print("Usage: python organize_drive_w.py [undo|status]")
    else:
        organize()
