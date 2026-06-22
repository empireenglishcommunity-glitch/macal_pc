"""
Default Tools — Pre-registered tools available to the agent.

These tools are registered at startup and define the agent's
core capabilities. Each tool maps to a real executor function
in the execution layer.

Categories:
- file: File system operations (create, move, rename, delete)
- system: System information and status
- gui: Desktop GUI automation (Phase 3)
"""

from __future__ import annotations

from src.intelligence.tool_registry import ToolRegistry


def register_file_tools(registry: ToolRegistry) -> None:
    """Register all file management tools."""

    registry.register(
        name="create_folder",
        description="Create a new folder at the specified path. Creates parent folders if they don't exist.",
        parameters={
            "path": {
                "type": "string",
                "description": "Full path for the new folder (e.g., '~/Organized/Documents/2026-06')",
            },
        },
        category="file",
    )

    registry.register(
        name="move_file",
        description="Move a file or folder from source to destination path.",
        parameters={
            "source": {
                "type": "string",
                "description": "Current path of the file/folder to move",
            },
            "destination": {
                "type": "string",
                "description": "New path where the file/folder should be placed",
            },
        },
        category="file",
    )

    registry.register(
        name="rename_file",
        description="Rename a file or folder (stays in the same directory).",
        parameters={
            "path": {
                "type": "string",
                "description": "Current path of the file/folder to rename",
            },
            "new_name": {
                "type": "string",
                "description": "New filename (with extension) or folder name",
            },
        },
        category="file",
    )

    registry.register(
        name="copy_file",
        description="Copy a file to a new location (original remains unchanged).",
        parameters={
            "source": {
                "type": "string",
                "description": "Path of the file to copy",
            },
            "destination": {
                "type": "string",
                "description": "Destination path for the copy",
            },
        },
        category="file",
    )

    registry.register(
        name="delete_file",
        description="Delete a file. CAUTION: This is destructive and requires user approval.",
        parameters={
            "path": {
                "type": "string",
                "description": "Path of the file to delete",
            },
            "reason": {
                "type": "string",
                "description": "Reason for deletion (shown to user for approval)",
            },
        },
        category="file",
    )

    registry.register(
        name="list_directory",
        description="List all files and folders in a directory.",
        parameters={
            "path": {
                "type": "string",
                "description": "Directory path to list contents of",
            },
        },
        category="file",
    )

    registry.register(
        name="read_file_info",
        description="Get metadata about a file (size, type, dates) without reading its content.",
        parameters={
            "path": {
                "type": "string",
                "description": "Path of the file to get info about",
            },
        },
        category="file",
    )


def register_system_tools(registry: ToolRegistry) -> None:
    """Register system information tools."""

    registry.register(
        name="get_system_status",
        description="Get current system status (CPU, RAM, disk usage).",
        parameters={},
        required=[],
        category="system",
    )


def create_default_registry() -> ToolRegistry:
    """Create a ToolRegistry with all default tools registered.

    This is the standard registry used by the agent daemon on startup.
    """
    registry = ToolRegistry()
    register_file_tools(registry)
    register_system_tools(registry)
    return registry
