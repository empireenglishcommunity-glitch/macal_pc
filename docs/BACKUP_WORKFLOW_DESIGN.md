# MACAL Backup System — Human-Controlled, Review-First Design

## Document Type: System Architecture (No Implementation Until Approved)
## Date: June 23, 2026

---

## 1. Design Principles

| Principle | Enforcement |
|-----------|------------|
| **Nothing uploads without explicit approval** | Every folder requires manual YES before encryption/upload |
| **Organization before backup** | Files are sorted and cleaned FIRST |
| **One folder at a time** | System presents folders individually for review |
| **Non-destructive** | Original files never deleted — only copied/moved within organized structure |
| **Full audit trail** | Every decision (approve/reject/skip) is logged permanently |
| **Resumable** | Can stop and continue anytime without losing progress |
| **Encrypted before upload** | Files are AES-256 encrypted locally, THEN uploaded |
| **No sensitive leaks** | Rejected/excluded files never touch the network |

---

## 2. Overall Workflow Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                    BACKUP WORKFLOW (4 PHASES)                     ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  PHASE 1: ORGANIZE                                                ║
║  ┌─────────────────────────────────────────────────────────────┐ ║
║  │ Scan V: and W: drives                                        │ ║
║  │ → Group by: type (photo/video) + date (YYYY-MM)              │ ║
║  │ → Move into structured folders                               │ ║
║  │ → Generate manifest (file count, size, types per folder)     │ ║
║  │ → Result: clean organized structure ready for review         │ ║
║  └─────────────────────────────────────────────────────────────┘ ║
║                              ↓                                    ║
║  PHASE 2: REVIEW (Human-in-the-loop)                              ║
║  ┌─────────────────────────────────────────────────────────────┐ ║
║  │ System presents ONE folder at a time:                        │ ║
║  │   "Photos/2024-03/ — 47 files, 2.3 GB"                      │ ║
║  │   [APPROVE] [REJECT] [SKIP] [OPEN FOLDER] [EXCLUDE FILES]   │ ║
║  │                                                               │ ║
║  │ You: open folder in Explorer → review contents               │ ║
║  │ You: decide → approve / reject / exclude specific files      │ ║
║  │                                                               │ ║
║  │ Approved → moves to PHASE 3 queue                            │ ║
║  │ Rejected → marked "rejected" in log, never touched again     │ ║
║  │ Skipped → revisit later                                      │ ║
║  └─────────────────────────────────────────────────────────────┘ ║
║                              ↓                                    ║
║  PHASE 3: ENCRYPT                                                 ║
║  ┌─────────────────────────────────────────────────────────────┐ ║
║  │ For each APPROVED folder:                                    │ ║
║  │   → 7-Zip AES-256 encrypt entire folder → one .7z file      │ ║
║  │   → Filename: "Photos_2024-03_47files.7z.enc"                │ ║
║  │   → Stored in local staging area until upload confirmed      │ ║
║  └─────────────────────────────────────────────────────────────┘ ║
║                              ↓                                    ║
║  PHASE 4: UPLOAD TO TELEGRAM                                      ║
║  ┌─────────────────────────────────────────────────────────────┐ ║
║  │ Upload encrypted .7z to Telegram Saved Messages              │ ║
║  │   → Caption: folder name + file count + date range           │ ║
║  │   → Split if >2GB (auto-reassemble on download)              │ ║
║  │   → Verify upload (hash check)                               │ ║
║  │   → Mark as "backed up" in database                          │ ║
║  │   → Optional: delete local encrypted .7z (originals remain)  │ ║
║  └─────────────────────────────────────────────────────────────┘ ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 3. Phase 1: Intelligent Organization

### 3.1 What the Organizer Does

```
INPUTS:
  V:\ (all contents)
  W:\ (all contents)

ANALYSIS:
  For each file:
    → Read extension (jpg, png, mp4, mov, heic, etc.)
    → Read modification date
    → Read EXIF date (if photo)
    → Calculate file hash (for duplicate detection)
    → Determine category: Photo / Video / Screenshot / Other

OUTPUT STRUCTURE (on same drive, non-destructive):
  V:\Organized\
    Photos\
      2024-01\
      2024-02\
      ...
    Videos\
      2024-01\
      ...
    Screenshots\
      2024-01\
      ...
    Other\

  W:\Organized\
    (same structure)
```

### 3.2 Organization Rules

| Rule | Behavior |
|------|----------|
| Non-destructive | Files are MOVED within the same drive (not deleted) |
| Originals preserved | A `.organization_log.db` records every move for undo |
| Duplicates detected | Hash-based detection; duplicates moved to `Duplicates/` subfolder |
| Unknown files | Go to `Other/` — reviewed manually later |
| Empty folders | Cleaned up after organization |
| Already-organized | Files already in correct structure are skipped |

### 3.3 Manifest Generation

After organization, the system generates a **manifest file** (`manifest.json`):

```json
{
  "drive": "V:",
  "organized_at": "2026-06-23T22:00:00",
  "total_files": 1776,
  "total_size_gb": 45.9,
  "folders": [
    {
      "path": "V:\\Organized\\Photos\\2024-03",
      "files": 47,
      "size_mb": 2340,
      "types": {"jpg": 30, "heic": 12, "png": 5},
      "status": "pending_review"
    },
    ...
  ]
}
```

This manifest drives Phase 2.

---

## 4. Phase 2: Folder-by-Folder Review System

### 4.1 Review Interface

The review system runs as a **terminal-based interactive tool** (like the bridge):

```
╔══════════════════════════════════════════════════════════════════╗
║                MACAL BACKUP REVIEW — Folder 1/38                 ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Folder:  V:\Organized\Photos\2024-03                            ║
║  Files:   47                                                      ║
║  Size:    2.3 GB                                                  ║
║  Types:   JPG (30), HEIC (12), PNG (5)                           ║
║  Dates:   March 1 - March 28, 2024                               ║
║                                                                   ║
║  ─────────────────────────────────────────────────────────────── ║
║                                                                   ║
║  Actions:                                                         ║
║    [A] APPROVE — encrypt and queue for backup                    ║
║    [R] REJECT  — mark as private, never upload                   ║
║    [S] SKIP    — review later                                    ║
║    [O] OPEN    — open folder in File Explorer to inspect         ║
║    [E] EXCLUDE — enter folder, select files to exclude           ║
║    [Q] QUIT    — save progress and exit                          ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
```

### 4.2 Review Actions

| Action | What Happens |
|--------|-------------|
| **A (Approve)** | Folder marked "approved" in database → enters Phase 3 queue |
| **R (Reject)** | Folder marked "rejected" → never shown again, never uploaded |
| **S (Skip)** | Folder marked "skipped" → appears again in next review session |
| **O (Open)** | Opens the folder in Windows File Explorer so you can see the actual photos/videos |
| **E (Exclude)** | Shows file list → you type numbers to exclude → excluded files moved to `Excluded/` subfolder |
| **Q (Quit)** | Saves all decisions so far → resume from where you left off next time |

### 4.3 Exclusion Workflow (Action E)

```
Files in V:\Organized\Photos\2024-03\:
  1. IMG_0001.jpg (3.2 MB)
  2. IMG_0002.jpg (2.8 MB)
  3. IMG_0003.heic (4.1 MB)
  ...
  47. screenshot_private.png (1.2 MB)

Exclude which files? (comma-separated numbers, or 'none'):
> 45, 46, 47

✓ 3 files excluded → moved to V:\Organized\Excluded\2024-03\
  Remaining: 44 files (2.1 GB) ready for approval.
  [A]pprove remaining? [S]kip? [R]eject?
> A
✓ Folder approved for backup.
```

### 4.4 Review State Persistence

All decisions are stored in SQLite (`backup_state.db`):

```sql
CREATE TABLE folder_reviews (
    id INTEGER PRIMARY KEY,
    drive TEXT,           -- "V:" or "W:"
    folder_path TEXT,     -- relative path
    file_count INTEGER,
    size_bytes INTEGER,
    status TEXT,          -- "pending", "approved", "rejected", "skipped"
    reviewed_at TEXT,     -- timestamp of decision
    excluded_files TEXT,  -- JSON list of excluded filenames
    encrypted_at TEXT,    -- NULL until encrypted
    uploaded_at TEXT,     -- NULL until uploaded
    telegram_msg_id TEXT  -- Telegram message ID (for recovery)
);
```

**Key behaviors:**
- If you quit mid-review, progress is saved
- If you restart the tool, it shows only "pending" and "skipped" folders
- Approved folders automatically queue for Phase 3
- Rejected folders never appear again (unless you manually reset)

---

## 5. Phase 3: Encryption Stage

### 5.1 Encryption Workflow

For each **approved** folder:

```
INPUT:  V:\Organized\Photos\2024-03\ (44 files, 2.1 GB)

PROCESS:
  1. Create 7-Zip archive with AES-256 encryption
  2. Password: your master password (entered once per session)
  3. Compression: minimal (photos/videos don't compress well)
  4. Output: staging_area\Photos_2024-03_44files.7z

RESULT:
  One encrypted .7z file ready for upload
  Original folder: UNTOUCHED (still on V: drive)
```

### 5.2 Staging Area

Encrypted archives are held in a **staging area** before upload:

```
C:\Users\97150\macal_pc\data\backup_staging\
  Photos_2024-03_44files.7z       (2.1 GB, encrypted)
  Photos_2024-04_62files.7z       (3.4 GB, encrypted)
  Videos_2024-03_8files.7z        (15.2 GB, encrypted)
```

**Why staging?**
- You can verify the archive (test decrypt) before uploading
- If upload fails, the encrypted file is still here
- After successful upload + verification, staging file can be deleted
- Prevents re-encrypting if you need to re-upload

### 5.3 Password Management

| Approach | Recommendation |
|----------|---------------|
| One master password for all archives | ✅ Simple, practical |
| Password stored anywhere? | ❌ NEVER stored in any file or database |
| How to handle forgotten password? | Files are unrecoverable — write password on paper, store safely |
| Password strength | Minimum 12 characters, mix of letters/numbers/symbols |

The script asks for your password **once** when you start a backup session. It holds it in memory only (never written to disk). When you close the script, the password is gone from memory.

---

## 6. Phase 4: Telegram Upload

### 6.1 Upload Architecture

```
STAGING FILE: Photos_2024-03_44files.7z (2.1 GB)
    │
    ▼ (under 2GB? upload directly)
    ▼ (over 2GB? split into parts)
    │
TELEGRAM SAVED MESSAGES:
    │
    ├── Message 1: "📁 Photos_2024-03_44files.7z"
    │   Caption: "Backup: Photos/2024-03 | 44 files | 2.1 GB | Encrypted AES-256"
    │   [File attached: Photos_2024-03_44files.7z]
    │
    ├── Message 2: "📁 Videos_2024-03_8files.7z.001" (part 1 of 3)
    │   Caption: "Backup: Videos/2024-03 | Part 1/3 | 15.2 GB total"
    │
    └── ...
```

### 6.2 Split Strategy (Files > 2 GB)

| Original Size | Action |
|:------------:|--------|
| < 2 GB | Upload as single file |
| 2-4 GB | Split into 2 parts (1.9 GB each) |
| 4-10 GB | Split into parts of 1.9 GB |
| > 10 GB | Split into parts of 1.9 GB |

7-Zip supports native volume splitting:
```
7z a -v1900m -pYOURPASSWORD archive.7z folder/
→ creates: archive.7z.001, archive.7z.002, archive.7z.003
```

### 6.3 Upload Verification

After each upload:
1. Download the file back from Telegram
2. Compare hash with local staging file
3. If match → mark as "verified" in database
4. If mismatch → flag for re-upload

### 6.4 Caption Format (For Future Recovery)

Each Telegram message has a structured caption:
```
📁 MACAL Backup
Folder: Photos/2024-03
Files: 44
Size: 2.1 GB
Encrypted: AES-256
Date: 2026-06-23
Part: 1/1
Hash: sha256:a4f2c8...
```

This caption allows automated recovery — a download script can parse these captions and reconstruct the folder structure.

---

## 7. Progress Tracking & Logging

### 7.1 Database Schema

```sql
-- Main tracking table
CREATE TABLE backup_log (
    id INTEGER PRIMARY KEY,
    folder_path TEXT NOT NULL,
    drive TEXT NOT NULL,
    file_count INTEGER,
    size_bytes INTEGER,
    -- Phase 2
    review_status TEXT DEFAULT 'pending',  -- pending/approved/rejected/skipped
    reviewed_at TEXT,
    excluded_files TEXT,  -- JSON
    -- Phase 3
    encryption_status TEXT DEFAULT 'pending',  -- pending/done/failed
    encrypted_at TEXT,
    archive_path TEXT,
    archive_hash TEXT,
    -- Phase 4
    upload_status TEXT DEFAULT 'pending',  -- pending/uploading/done/failed
    uploaded_at TEXT,
    telegram_msg_ids TEXT,  -- JSON array of message IDs
    verified INTEGER DEFAULT 0
);

-- Exclusion tracking
CREATE TABLE excluded_files (
    id INTEGER PRIMARY KEY,
    folder_path TEXT,
    filename TEXT,
    reason TEXT,
    excluded_at TEXT
);

-- Session history
CREATE TABLE backup_sessions (
    id INTEGER PRIMARY KEY,
    started_at TEXT,
    ended_at TEXT,
    folders_reviewed INTEGER,
    folders_approved INTEGER,
    folders_rejected INTEGER,
    bytes_uploaded INTEGER
);
```

### 7.2 Progress Report (Available Anytime)

```
═══════════════════════════════════════════════════
  MACAL BACKUP PROGRESS
═══════════════════════════════════════════════════

  Drive V:
    Total folders: 38
    Reviewed: 24 (63%)
      Approved: 18
      Rejected: 4
      Skipped: 2
    Encrypted: 15
    Uploaded: 12
    Remaining: 14 folders (42 GB)

  Drive W:
    Total folders: 22
    Reviewed: 0 (not started)

  Overall:
    Total data: 250 GB
    Backed up: 89 GB (36%)
    Estimated time remaining: ~4 upload sessions
═══════════════════════════════════════════════════
```

---

## 8. Failure Recovery & Resume

| Failure Scenario | Recovery |
|-----------------|----------|
| Script crashes during review | All prior decisions saved in SQLite — restart and continue |
| Encryption interrupted | Delete partial archive, re-encrypt the folder |
| Upload interrupted mid-file | Telegram API supports resume; or re-upload the part |
| Internet disconnects | Script detects, saves state, resumes on next run |
| Password forgotten | Files on Telegram are unrecoverable — KEEP YOUR PASSWORD SAFE |
| Telegram account issue | Files still exist locally (originals never deleted) |
| Drive V: disconnected | Script detects, alerts you, waits for reconnection |

### Resume Mechanism

Every time you start the tool:
```
1. Read backup_state.db
2. Show: "Last session: 12 folders uploaded, 6 remaining in approved queue"
3. Options:
   [C] Continue uploading approved folders
   [R] Review more folders
   [P] Show progress report
   [Q] Quit
```

---

## 9. Recommended Implementation Order

| Step | What | Time | Depends On |
|:----:|------|:----:|:----------:|
| 1 | Build the organizer (scan V: and W:, sort by type+date) | 30 min | Nothing |
| 2 | Build the manifest generator | 15 min | Step 1 |
| 3 | Build the review tool (terminal UI) | 45 min | Step 2 |
| 4 | Build the encryption stage (7-Zip wrapper) | 20 min | Step 3 |
| 5 | Set up Telegram API credentials | 15 min | Nothing |
| 6 | Build the upload engine (Telethon) | 45 min | Steps 4, 5 |
| 7 | Build progress tracker + resume logic | 30 min | Step 6 |
| 8 | Test with ONE small folder end-to-end | 15 min | All |

**Total build time: ~3.5 hours**
**Total upload time: ~7-10 hours (runs overnight in sessions)**

---

## 10. Security Summary

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY LAYERS                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Human Review (Phase 2)                             │
│  → You personally inspect every folder before it's touched   │
│  → Sensitive content never enters the pipeline               │
│                                                              │
│  Layer 2: Exclusion System                                   │
│  → Individual files can be excluded from approved folders    │
│  → Excluded files moved to separate directory (never uploaded)│
│                                                              │
│  Layer 3: AES-256 Encryption (Phase 3)                       │
│  → Military-grade encryption before any data leaves your PC  │
│  → Password only in your memory (never stored digitally)     │
│  → Even if Telegram is breached, files are unreadable        │
│                                                              │
│  Layer 4: Telegram Security                                  │
│  → 2FA on your account                                       │
│  → Saved Messages only accessible by you                     │
│  → MTProto 2.0 encrypted transport                           │
│                                                              │
│  Layer 5: Verification                                       │
│  → Hash verification after upload (integrity check)          │
│  → Download test confirms recoverability                     │
│                                                              │
│  Layer 6: Originals Never Deleted                            │
│  → Original files remain on V: and W: drives                 │
│  → Only delete after YOU manually verify backup is complete   │
│  → No automatic deletion ever                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. What This Means Practically

**A typical session looks like:**

```
Evening 1: Run organizer on V: drive (30 min, automated)
Evening 2: Review 10 folders (20 min, you inspect each)
           → Approve 7, reject 2, skip 1
Evening 3: Encryption runs on approved folders (automated, 15 min)
           → Upload starts (runs overnight, 6-8 hours)
           → Wake up to Telegram notification: "8 folders backed up"
Evening 4: Review next 10 folders...
(repeat until done)
```

**You never rush. You never upload without seeing what's inside. The system waits for you.**

---

*This is a DESIGN ONLY. No implementation begins until you approve. Tell me to start and I'll build Phase 1 first.*
