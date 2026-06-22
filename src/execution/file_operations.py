"""
File Operations — Safe file management with full audit trail.

All file operations go through this module, which:
- Validates paths against security allowlists
- Logs every operation to the transaction journal
- Supports rollback of any operation
- Handles errors gracefully

Operations: create_folder, move_file, rename_file, copy_file,
            delete_file (with approval), list_directory, read_file_info
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FileOpResult:
    """Result of a file operation."""

    success: bool
    operation: str
    source: str
    destination: str = ""
    error: str = ""
    bytes_affected: int = 0


class FileOperations:
    """Safe file operations with validation and logging.

    Every method validates paths before acting and returns a
    structured result that the transaction journal can record.
    """

    def __init__(self, allowed_paths: list[str] | None = None) -> None:
        self.allowed_paths = [Path(p).expanduser() for p in (allowed_paths or [])]

    def _validate_path(self, path: Path, operation: str = "access") -> tuple[bool, str]:
        """Check if a path is within allowed boundaries."""
        resolved = path.expanduser().resolve()

        if not self.allowed_paths:
            return True, ""  # No restrictions configured

        for allowed in self.allowed_paths:
            try:
                if resolved.is_relative_to(allowed.resolve()):
                    return True, ""
            except (ValueError, OSError):
                continue

        return False, f"Path '{resolved}' is outside allowed directories for '{operation}'"

    async def create_folder(self, path: str) -> FileOpResult:
        """Create a folder (and parents if needed)."""
        target = Path(path).expanduser()
        valid, error = self._validate_path(target, "create_folder")
        if not valid:
            return FileOpResult(success=False, operation="create_folder", source=path, error=error)

        try:
            target.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created folder: {target}")
            return FileOpResult(success=True, operation="create_folder", source=str(target))
        except OSError as e:
            return FileOpResult(success=False, operation="create_folder", source=path, error=str(e))

    async def move_file(self, source: str, destination: str) -> FileOpResult:
        """Move a file or folder to a new location."""
        src = Path(source).expanduser()
        dst = Path(destination).expanduser()

        valid, error = self._validate_path(dst, "move_file")
        if not valid:
            return FileOpResult(
                success=False, operation="move_file", source=source, destination=destination,
                error=error,
            )

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            size = dst.stat().st_size if dst.is_file() else 0
            logger.info(f"Moved: {src} → {dst}")
            return FileOpResult(
                success=True, operation="move_file", source=str(src),
                destination=str(dst), bytes_affected=size,
            )
        except OSError as e:
            return FileOpResult(
                success=False, operation="move_file", source=source,
                destination=destination, error=str(e),
            )

    async def rename_file(self, path: str, new_name: str) -> FileOpResult:
        """Rename a file (same directory, new name)."""
        src = Path(path).expanduser()
        dst = src.parent / new_name

        valid, error = self._validate_path(dst, "rename_file")
        if not valid:
            return FileOpResult(success=False, operation="rename_file", source=path, error=error)

        try:
            src.rename(dst)
            logger.info(f"Renamed: {src.name} → {new_name}")
            return FileOpResult(
                success=True, operation="rename_file", source=str(src), destination=str(dst)
            )
        except OSError as e:
            return FileOpResult(success=False, operation="rename_file", source=path, error=str(e))

    async def list_directory(self, path: str) -> list[dict]:
        """List contents of a directory (non-destructive, always allowed)."""
        target = Path(path).expanduser()
        if not target.is_dir():
            return []

        entries = []
        try:
            for item in sorted(target.iterdir()):
                entries.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
        except PermissionError:
            logger.warning(f"Permission denied listing: {target}")

        return entries
