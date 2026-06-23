"""
Backup Review Tool — Folder-by-folder review with human approval.
Presents each organized folder for manual inspection before backup.

Actions:
    A = Approve (queue for encryption + upload)
    R = Reject (never upload, mark as private)
    S = Skip (review later)
    O = Open folder in File Explorer (inspect contents)
    Q = Quit (save progress, resume next time)

Usage:
    python scripts/review_backup.py
"""
import os
import sys
import sqlite3
import subprocess
from pathlib import Path

# Configuration
DB_PATH = Path("W:/.organize_log.db")
ORGANIZE_ROOT = Path("W:/Organized")


def get_pending_folders():
    """Get folders that need review."""
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT id, folder_path, file_count, size_bytes, status FROM manifest "
        "WHERE status IN ('pending_review', 'skipped') ORDER BY folder_path"
    ).fetchall()
    conn.close()
    return rows


def get_all_folders():
    """Get all folders with their status."""
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT id, folder_path, file_count, size_bytes, status FROM manifest ORDER BY folder_path"
    ).fetchall()
    conn.close()
    return rows


def update_status(folder_id, new_status):
    """Update a folder's review status."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "UPDATE manifest SET status=? WHERE id=?",
        (new_status, folder_id)
    )
    conn.commit()
    conn.close()


def open_folder(folder_path):
    """Open folder in Windows File Explorer."""
    try:
        subprocess.Popen(["explorer", str(folder_path)])
    except Exception as e:
        print("  Error opening folder: " + str(e))


def show_summary():
    """Show review progress."""
    conn = sqlite3.connect(str(DB_PATH))
    pending = conn.execute("SELECT COUNT(*) FROM manifest WHERE status='pending_review'").fetchone()[0]
    skipped = conn.execute("SELECT COUNT(*) FROM manifest WHERE status='skipped'").fetchone()[0]
    approved = conn.execute("SELECT COUNT(*) FROM manifest WHERE status='approved'").fetchone()[0]
    rejected = conn.execute("SELECT COUNT(*) FROM manifest WHERE status='rejected'").fetchone()[0]
    total_approved_size = conn.execute("SELECT SUM(size_bytes) FROM manifest WHERE status='approved'").fetchone()[0] or 0
    conn.close()

    print("")
    print("  Progress:")
    print("    Pending:  " + str(pending))
    print("    Skipped:  " + str(skipped))
    print("    Approved: " + str(approved) + " (" + str(round(total_approved_size / (1024**3), 2)) + " GB)")
    print("    Rejected: " + str(rejected))
    print("")


def review_folder(folder_id, folder_path, file_count, size_bytes, index, total):
    """Present one folder for review."""
    size_mb = round(size_bytes / (1024**2), 1)
    folder_name = str(Path(folder_path).relative_to(ORGANIZE_ROOT))

    # Count file types
    types = {}
    folder_p = Path(folder_path)
    if folder_p.exists():
        for f in folder_p.iterdir():
            if f.is_file():
                ext = f.suffix.lower()
                types[ext] = types.get(ext, 0) + 1

    types_str = ", ".join(ext + "(" + str(c) + ")" for ext, c in sorted(types.items(), key=lambda x: -x[1])[:5])

    print("")
    print("  " + "=" * 58)
    print("  FOLDER " + str(index) + "/" + str(total))
    print("  " + "=" * 58)
    print("")
    print("  Path:   " + folder_name)
    print("  Files:  " + str(file_count))
    print("  Size:   " + str(size_mb) + " MB")
    print("  Types:  " + types_str)
    print("")
    print("  " + "-" * 58)
    print("  [A] Approve    — queue for encrypted backup")
    print("  [R] Reject     — mark private, never upload")
    print("  [S] Skip       — review later")
    print("  [O] Open       — view in File Explorer")
    print("  [Q] Quit       — save and exit")
    print("  " + "-" * 58)

    while True:
        choice = input("  Your decision: ").strip().upper()

        if choice == "A":
            update_status(folder_id, "approved")
            print("  --> APPROVED for backup")
            return "continue"
        elif choice == "R":
            update_status(folder_id, "rejected")
            print("  --> REJECTED (will never be uploaded)")
            return "continue"
        elif choice == "S":
            update_status(folder_id, "skipped")
            print("  --> SKIPPED (will appear again next time)")
            return "continue"
        elif choice == "O":
            print("  --> Opening in File Explorer...")
            open_folder(folder_path)
            print("  (Review the contents, then come back and decide)")
            print("")
        elif choice == "Q":
            print("  --> Saving progress and exiting...")
            return "quit"
        else:
            print("  Please enter A, R, S, O, or Q")


def main():
    if not DB_PATH.exists():
        print("ERROR: No organization data found at " + str(DB_PATH))
        print("Run organize_drive_w.py first.")
        return

    print("")
    print("=" * 60)
    print("  MACAL BACKUP REVIEW — W: Drive")
    print("  Review each folder before backup")
    print("=" * 60)

    show_summary()

    folders = get_pending_folders()
    if not folders:
        print("  No folders pending review. All done!")
        print("  Run the backup script to encrypt and upload approved folders.")
        return

    print("  " + str(len(folders)) + " folder(s) to review.")
    print("  (Open each folder to inspect, then approve/reject)")

    for i, (folder_id, folder_path, file_count, size_bytes, status) in enumerate(folders, 1):
        result = review_folder(folder_id, folder_path, file_count, size_bytes, i, len(folders))
        if result == "quit":
            break

    show_summary()
    print("  Resume anytime: python scripts/review_backup.py")
    print("")


if __name__ == "__main__":
    main()
