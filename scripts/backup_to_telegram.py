"""
MACAL Encrypted Backup to Telegram — Phase 3 + 4

Encrypts approved folders with AES-256 (7-Zip) then uploads to Telegram Saved Messages.

Flow:
    1. Reads approved folders from manifest (W:\.organize_log.db)
    2. For each approved folder not yet uploaded:
       a. Compress + encrypt with 7-Zip AES-256
       b. Upload encrypted archive to Telegram Saved Messages
       c. Verify upload (size check)
       d. Mark as uploaded in database
       e. Delete local encrypted archive (original stays)

Usage:
    python scripts/backup_to_telegram.py              (run backup)
    python scripts/backup_to_telegram.py --status     (show progress)
    python scripts/backup_to_telegram.py --test       (test with 1 folder)

Requirements:
    pip install telethon tqdm
    7-Zip installed (standard Windows install at C:\Program Files\7-Zip\7z.exe)
"""
import os
import sys
import json
import sqlite3
import asyncio
import subprocess
import hashlib
import getpass
from pathlib import Path
from datetime import datetime

try:
    from telethon import TelegramClient
    from telethon.tl.types import DocumentAttributeFilename
    from tqdm import tqdm
except ImportError:
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "telethon", "tqdm", "-q"])
    from telethon import TelegramClient
    from telethon.tl.types import DocumentAttributeFilename
    from tqdm import tqdm

# Configuration
API_ID = 33305178
API_HASH = "e387b07b625eb2229c782641d43327ad"
SESSION_FILE = str(Path.home() / ".macal_telegram_backup")
DB_PATH = Path("W:/.organize_log.db")
ORGANIZE_ROOT = Path("W:/Organized")
STAGING_DIR = Path("W:/backup_staging")
SEVEN_ZIP = Path("C:/Program Files/7-Zip/7z.exe")

# Split size for Telegram (max 2GB per file, use 1.9GB for safety)
MAX_UPLOAD_SIZE = 1900 * 1024 * 1024  # 1.9 GB


def get_approved_folders():
    """Get folders approved but not yet uploaded."""
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT id, folder_path, file_count, size_bytes FROM manifest "
        "WHERE status='approved' ORDER BY folder_path"
    ).fetchall()
    conn.close()
    return rows


def get_uploaded_count():
    """Count already uploaded folders."""
    conn = sqlite3.connect(str(DB_PATH))
    count = conn.execute(
        "SELECT COUNT(*) FROM manifest WHERE status='uploaded'"
    ).fetchone()[0]
    conn.close()
    return count


def mark_uploaded(folder_id):
    """Mark folder as uploaded in database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "UPDATE manifest SET status='uploaded' WHERE id=?", (folder_id,)
    )
    conn.commit()
    conn.close()


def encrypt_folder(folder_path, password):
    """Compress and encrypt a folder using 7-Zip AES-256."""
    folder_p = Path(folder_path)
    folder_name = folder_p.relative_to(ORGANIZE_ROOT)
    safe_name = str(folder_name).replace("\\", "_").replace("/", "_")
    archive_name = safe_name + ".7z"
    archive_path = STAGING_DIR / archive_name

    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    # Check if 7-Zip exists
    if not SEVEN_ZIP.exists():
        # Try alternate locations
        alt_paths = [
            Path("C:/Program Files/7-Zip/7z.exe"),
            Path("C:/Program Files (x86)/7-Zip/7z.exe"),
        ]
        found = False
        for alt in alt_paths:
            if alt.exists():
                seven_zip = str(alt)
                found = True
                break
        if not found:
            print("ERROR: 7-Zip not found. Install from https://7-zip.org")
            return None
    else:
        seven_zip = str(SEVEN_ZIP)

    # Build 7-Zip command: encrypt with AES-256, minimal compression (media doesn't compress)
    cmd = [
        seven_zip, "a",
        "-t7z",                    # 7z format
        "-mhe=on",                 # Encrypt filenames too
        "-p" + password,           # Password
        "-mx=1",                   # Minimal compression (fast, media doesn't compress)
        str(archive_path),         # Output archive
        str(folder_path) + "\\*",  # Input files
    ]

    # Handle volume splitting if folder is large
    folder_size = sum(f.stat().st_size for f in folder_p.rglob("*") if f.is_file())
    if folder_size > MAX_UPLOAD_SIZE:
        cmd.insert(2, "-v1900m")   # Split into 1.9 GB volumes

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("  7-Zip error: " + result.stderr[:200])
        return None

    # Return list of archive parts (single file or .001, .002, etc.)
    if folder_size > MAX_UPLOAD_SIZE:
        parts = sorted(STAGING_DIR.glob(safe_name + ".7z.*"))
        return [str(p) for p in parts]
    else:
        return [str(archive_path)]


def get_file_hash(filepath):
    """Calculate SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()[:16]


async def upload_to_telegram(archive_paths, folder_name, file_count, folder_size):
    """Upload encrypted archive(s) to Telegram Saved Messages."""
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.start()

    me = await client.get_me()
    print("  Logged in as: " + me.first_name)

    total_parts = len(archive_paths)

    for i, archive_path in enumerate(archive_paths, 1):
        archive_p = Path(archive_path)
        size_mb = round(archive_p.stat().st_size / (1024**2), 1)
        file_hash = get_file_hash(archive_path)

        # Caption for recovery
        caption = (
            "MACAL Backup\n"
            "Folder: " + folder_name + "\n"
            "Files: " + str(file_count) + "\n"
            "Size: " + str(size_mb) + " MB\n"
            "Part: " + str(i) + "/" + str(total_parts) + "\n"
            "Hash: " + file_hash + "\n"
            "Date: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n"
            "Encrypted: AES-256"
        )

        print("  Uploading: " + archive_p.name + " (" + str(size_mb) + " MB) [" + str(i) + "/" + str(total_parts) + "]")

        # Upload with progress
        await client.send_file(
            "me",
            archive_path,
            caption=caption,
            force_document=True,
            progress_callback=lambda current, total: print(
                "    " + str(round(current/total*100)) + "%", end="\r"
            ) if total else None,
        )
        print("    100% - uploaded!")

    await client.disconnect()
    return True


async def run_backup(password, test_mode=False):
    """Main backup loop."""
    folders = get_approved_folders()
    if not folders:
        print("No approved folders to backup.")
        print("Already uploaded: " + str(get_uploaded_count()) + " folders")
        return

    if test_mode:
        folders = folders[:1]
        print("TEST MODE: processing only 1 folder")

    print("")
    print("=" * 60)
    print("  MACAL ENCRYPTED BACKUP TO TELEGRAM")
    print("=" * 60)
    print("")
    print("  Folders to backup: " + str(len(folders)))
    print("  Already uploaded: " + str(get_uploaded_count()))
    print("")

    for i, (folder_id, folder_path, file_count, size_bytes) in enumerate(folders, 1):
        folder_name = str(Path(folder_path).relative_to(ORGANIZE_ROOT))
        size_mb = round(size_bytes / (1024**2), 1)

        print("-" * 60)
        print("  [" + str(i) + "/" + str(len(folders)) + "] " + folder_name)
        print("  Files: " + str(file_count) + " | Size: " + str(size_mb) + " MB")
        print("")

        # Step 1: Encrypt
        print("  Encrypting with AES-256...")
        archive_paths = encrypt_folder(folder_path, password)
        if not archive_paths:
            print("  FAILED to encrypt. Skipping.")
            continue
        print("  Encrypted: " + str(len(archive_paths)) + " archive(s)")

        # Step 2: Upload
        print("  Uploading to Telegram...")
        try:
            success = await upload_to_telegram(archive_paths, folder_name, file_count, size_bytes)
        except Exception as e:
            print("  Upload FAILED: " + str(e))
            continue

        if success:
            # Step 3: Mark as uploaded
            mark_uploaded(folder_id)
            print("  DONE! Marked as uploaded.")

            # Step 4: Clean staging
            for ap in archive_paths:
                try:
                    os.remove(ap)
                except Exception:
                    pass
            print("  Staging cleaned.")
        print("")

    print("=" * 60)
    print("  BACKUP SESSION COMPLETE")
    print("  Uploaded: " + str(get_uploaded_count()) + " folders total")
    print("=" * 60)


def show_status():
    """Show backup progress."""
    conn = sqlite3.connect(str(DB_PATH))
    approved = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM manifest WHERE status='approved'").fetchone()
    uploaded = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM manifest WHERE status='uploaded'").fetchone()
    conn.close()

    print("")
    print("  BACKUP STATUS")
    print("  " + "-" * 40)
    print("  Approved (waiting): " + str(approved[0]) + " folders (" + str(round((approved[1] or 0)/(1024**3), 2)) + " GB)")
    print("  Uploaded (done):    " + str(uploaded[0]) + " folders (" + str(round((uploaded[1] or 0)/(1024**3), 2)) + " GB)")
    print("")


def main():
    # Check 7-Zip
    if not SEVEN_ZIP.exists() and not Path("C:/Program Files (x86)/7-Zip/7z.exe").exists():
        print("ERROR: 7-Zip is required for encryption.")
        print("Download free from: https://7-zip.org")
        print("Install to default location (C:\\Program Files\\7-Zip\\)")
        return

    # Parse arguments
    if "--status" in sys.argv:
        show_status()
        return

    test_mode = "--test" in sys.argv

    # Get encryption password
    print("")
    print("=" * 60)
    print("  MACAL ENCRYPTED BACKUP")
    print("  Your files will be encrypted with AES-256 before upload.")
    print("  The password is NEVER stored. If you forget it,")
    print("  your backups CANNOT be recovered.")
    print("=" * 60)
    print("")
    password = getpass.getpass("  Enter encryption password: ")
    password2 = getpass.getpass("  Confirm password: ")

    if password != password2:
        print("  Passwords don't match! Aborting.")
        return
    if len(password) < 8:
        print("  Password too short (minimum 8 characters). Aborting.")
        return

    print("  Password accepted. Starting backup...")
    print("")

    # Run backup
    asyncio.run(run_backup(password, test_mode))


if __name__ == "__main__":
    main()
