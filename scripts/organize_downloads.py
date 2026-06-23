"""
AI File Organizer - Classifies and sorts files using local Ollama.
Watches ~/Downloads and organizes into ~/Organized/
"""
import os
import json
import shutil
import time
import sqlite3
import re
import requests
from pathlib import Path
from datetime import datetime

# Configuration
WATCH_DIR = Path.home() / "Downloads"
ORGANIZE_ROOT = Path.home() / "Organized"
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b"
DB_PATH = Path.home() / ".macal_organizer.db"
IGNORE = {".tmp", ".crdownload", ".part", ".ini"}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS operations ("
        "id INTEGER PRIMARY KEY, "
        "timestamp TEXT DEFAULT CURRENT_TIMESTAMP, "
        "original_path TEXT, "
        "new_path TEXT, "
        "category TEXT, "
        "undone INTEGER DEFAULT 0)"
    )
    conn.commit()
    return conn


def classify_file(filepath):
    name = filepath.name
    size = filepath.stat().st_size
    ext = filepath.suffix.lower()

    prompt = (
        "Classify this file. Return ONLY valid JSON.\n"
        "Filename: " + name + "\n"
        "Extension: " + ext + "\n"
        "Size: " + str(size) + " bytes\n\n"
        'Return: {"category": "Documents|Code|Images|Videos|Audio|Archives|Data|Other", '
        '"subcategory": "specific type"}'
    )

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "think": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 100}
        }, timeout=120)
        content = resp.json().get("message", {}).get("content", "")
        content = content.strip()
        if "<" in content and ">" in content:
            content = re.sub(r"<[^>]+>", "", content).strip()
        data = json.loads(content)
        return data.get("category", "Other"), data.get("subcategory", "General")
    except Exception as e:
        print("  Classification error: " + str(e))
        return guess_by_extension(ext)


def guess_by_extension(ext):
    mapping = {
        ".pdf": ("Documents", "PDF"),
        ".doc": ("Documents", "Word"),
        ".docx": ("Documents", "Word"),
        ".xls": ("Data", "Spreadsheet"),
        ".xlsx": ("Data", "Spreadsheet"),
        ".txt": ("Documents", "Text"),
        ".md": ("Documents", "Markdown"),
        ".py": ("Code", "Python"),
        ".js": ("Code", "JavaScript"),
        ".html": ("Code", "Web"),
        ".css": ("Code", "Web"),
        ".jpg": ("Images", "Photo"),
        ".jpeg": ("Images", "Photo"),
        ".png": ("Images", "Image"),
        ".gif": ("Images", "GIF"),
        ".mp4": ("Videos", "Video"),
        ".mkv": ("Videos", "Video"),
        ".mov": ("Videos", "Video"),
        ".mp3": ("Audio", "Music"),
        ".wav": ("Audio", "Audio"),
        ".zip": ("Archives", "Compressed"),
        ".rar": ("Archives", "Compressed"),
        ".7z": ("Archives", "Compressed"),
        ".tar": ("Archives", "Compressed"),
        ".exe": ("Other", "Installer"),
        ".msi": ("Other", "Installer"),
        ".vcf": ("Data", "Contact"),
        ".csv": ("Data", "CSV"),
        ".xml": ("Data", "XML"),
        ".log": ("Data", "Log"),
    }
    return mapping.get(ext, ("Other", "General"))


def organize_file(filepath, conn):
    if filepath.suffix.lower() in IGNORE:
        return None
    if filepath.name.startswith("~$") or filepath.name == "desktop.ini":
        return None
    if filepath.stat().st_size == 0:
        return None

    print("  Classifying: " + filepath.name)
    category, subcategory = classify_file(filepath)
    month = datetime.now().strftime("%Y-%m")
    dest_dir = ORGANIZE_ROOT / category / month
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filepath.name

    if dest_path.exists():
        stem = filepath.stem
        dest_path = dest_dir / (stem + "_" + str(int(time.time())) + filepath.suffix)

    conn.execute(
        "INSERT INTO operations (original_path, new_path, category) VALUES (?,?,?)",
        (str(filepath), str(dest_path), category)
    )
    conn.commit()

    shutil.move(str(filepath), str(dest_path))
    print("  Moved: " + filepath.name + " -> " + category + "/" + month + "/")
    return category


def scan_and_organize(max_files=0):
    conn = init_db()
    ORGANIZE_ROOT.mkdir(parents=True, exist_ok=True)
    files = [f for f in WATCH_DIR.iterdir() if f.is_file()]
    files = [f for f in files if f.suffix.lower() not in IGNORE]
    files = [f for f in files if not f.name.startswith("~$")]
    files = [f for f in files if f.name != "desktop.ini"]
    files = [f for f in files if f.stat().st_size > 0]

    if not files:
        print("No files to organize.")
        return

    if max_files > 0:
        files = files[:max_files]

    print("Found " + str(len(files)) + " file(s) to organize:")
    stats = {}
    for f in files:
        cat = organize_file(f, conn)
        if cat:
            stats[cat] = stats.get(cat, 0) + 1

    print("\nDone! Organized " + str(sum(stats.values())) + " files:")
    for cat, count in sorted(stats.items()):
        print("  " + cat + ": " + str(count))
    conn.close()


def undo_last(n=10):
    conn = sqlite3.connect(DB_PATH)
    ops = conn.execute(
        "SELECT id, original_path, new_path FROM operations WHERE undone=0 ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    if not ops:
        print("Nothing to undo.")
        return
    for op_id, orig, new in ops:
        if Path(new).exists():
            Path(orig).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(new, orig)
            conn.execute("UPDATE operations SET undone=1 WHERE id=?", (op_id,))
            print("  Undone: " + Path(new).name + " -> " + orig)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "undo":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        undo_last(n)
    elif len(sys.argv) > 1:
        try:
            max_files = int(sys.argv[1])
            scan_and_organize(max_files)
        except ValueError:
            scan_and_organize()
    else:
        scan_and_organize()
