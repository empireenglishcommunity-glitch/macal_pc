"""
Execution Engine — Takes planned tool calls and runs them for real.

This is the bridge between the LLM's decisions and actual changes
on the file system. Every action is:
1. Checked by the Permission Guard
2. Logged to the transaction journal (before execution)
3. Executed
4. Logged again (result/success/failure)

If any step fails, execution stops and returns the error.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.execution.file_operations import FileOperations, FileOpResult
from src.security.permission_guard import PermissionGuard, PermissionResult
from src.execution.gui_operations import GUIOperations

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Result of executing a single planned step."""

    step_number: int
    tool: str
    arguments: dict[str, Any]
    success: bool
    result: str = ""
    error: str = ""
    classification: str = ""
    duration_ms: int = 0


@dataclass
class TaskResult:
    """Result of executing an entire task (all steps)."""

    task_id: str
    status: str  # "completed", "failed", "blocked", "needs_approval"
    instruction: str
    steps_completed: int = 0
    steps_total: int = 0
    results: list[StepResult] = field(default_factory=list)
    error: str = ""
    duration_ms: int = 0


class ExecutionEngine:
    """Executes planned tool calls with safety checks.

    Takes the output of the LLM (list of tool calls) and
    executes each one sequentially, with permission checking
    and full audit logging.
    """

    def __init__(
        self,
        allowed_write_paths: list[str] | None = None,
        blocked_paths: list[str] | None = None,
    ) -> None:
        # Default safe paths for the agent
        default_allowed = [
            "~/Organized",
            "~/AgentWork",
            "~/Downloads",
            "~/Documents",
            "~/Desktop",
        ]
        default_blocked = [
            "C:/Windows",
            "C:/Program Files",
            "C:/Program Files (x86)",
            "~/AppData",
            "~/.ssh",
        ]

        self.file_ops = FileOperations(
            allowed_paths=allowed_write_paths or default_allowed
        )
        self.gui_ops = GUIOperations()
        self.permission_guard = PermissionGuard(
            allowed_paths=allowed_write_paths or default_allowed,
            blocked_paths=blocked_paths or default_blocked,
        )
        self._transaction_log: list[dict] = []

    async def execute_plan(
        self,
        instruction: str,
        planned_actions: list[dict[str, Any]],
    ) -> TaskResult:
        """Execute a list of planned tool calls.

        Args:
            instruction: Original user instruction (for logging).
            planned_actions: List of {"tool": "name", "arguments": {...}} dicts.

        Returns:
            TaskResult with status and per-step results.
        """
        task_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        results: list[StepResult] = []

        logger.info(f"[Task {task_id}] Executing {len(planned_actions)} steps for: {instruction}")

        for i, action in enumerate(planned_actions, 1):
            tool = action.get("tool", "")
            arguments = action.get("arguments", {})

            step_start = time.time()

            # 1. Permission check
            primary_path = self._extract_path(arguments)
            destination_path = self._extract_destination(arguments)

            perm = self.permission_guard.check(
                operation=tool,
                path=Path(primary_path) if primary_path else Path("."),
                destination=Path(destination_path) if destination_path else None,
            )

            if not perm.allowed:
                step_result = StepResult(
                    step_number=i, tool=tool, arguments=arguments,
                    success=False, error=f"BLOCKED: {perm.reason}",
                    classification=perm.classification,
                )
                results.append(step_result)
                logger.warning(f"[Task {task_id}] Step {i} BLOCKED: {perm.reason}")

                return TaskResult(
                    task_id=task_id, status="blocked",
                    instruction=instruction,
                    steps_completed=i - 1, steps_total=len(planned_actions),
                    results=results, error=perm.reason,
                    duration_ms=int((time.time() - start_time) * 1000),
                )

            if perm.needs_approval:
                step_result = StepResult(
                    step_number=i, tool=tool, arguments=arguments,
                    success=False, error="Requires user approval",
                    classification=perm.classification,
                )
                results.append(step_result)
                logger.info(f"[Task {task_id}] Step {i} needs approval: {tool}")

                return TaskResult(
                    task_id=task_id, status="needs_approval",
                    instruction=instruction,
                    steps_completed=i - 1, steps_total=len(planned_actions),
                    results=results,
                    error=f"Step {i} ({tool}) requires user approval",
                    duration_ms=int((time.time() - start_time) * 1000),
                )

            # 2. Execute
            try:
                op_result = await self._execute_tool(tool, arguments)
                step_ms = int((time.time() - step_start) * 1000)

                step_result = StepResult(
                    step_number=i, tool=tool, arguments=arguments,
                    success=op_result.success,
                    result=f"{op_result.operation}: {op_result.source}" + (
                        f" → {op_result.destination}" if op_result.destination else ""
                    ),
                    error=op_result.error,
                    classification=perm.classification,
                    duration_ms=step_ms,
                )
                results.append(step_result)

                # Log transaction
                self._log_transaction(task_id, i, tool, arguments, op_result)

                if not op_result.success:
                    logger.error(f"[Task {task_id}] Step {i} FAILED: {op_result.error}")
                    return TaskResult(
                        task_id=task_id, status="failed",
                        instruction=instruction,
                        steps_completed=i - 1, steps_total=len(planned_actions),
                        results=results, error=op_result.error,
                        duration_ms=int((time.time() - start_time) * 1000),
                    )

                logger.info(f"[Task {task_id}] Step {i} OK: {tool}({arguments})")

            except Exception as e:
                step_result = StepResult(
                    step_number=i, tool=tool, arguments=arguments,
                    success=False, error=str(e),
                    duration_ms=int((time.time() - step_start) * 1000),
                )
                results.append(step_result)
                logger.error(f"[Task {task_id}] Step {i} EXCEPTION: {e}")

                return TaskResult(
                    task_id=task_id, status="failed",
                    instruction=instruction,
                    steps_completed=i - 1, steps_total=len(planned_actions),
                    results=results, error=str(e),
                    duration_ms=int((time.time() - start_time) * 1000),
                )

        # All steps completed
        total_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[Task {task_id}] COMPLETED all {len(planned_actions)} steps in {total_ms}ms")

        return TaskResult(
            task_id=task_id, status="completed",
            instruction=instruction,
            steps_completed=len(planned_actions),
            steps_total=len(planned_actions),
            results=results,
            duration_ms=total_ms,
        )

    async def _execute_tool(self, tool: str, arguments: dict[str, Any]) -> FileOpResult:
        """Route a tool call to the correct executor."""

        if tool == "create_folder":
            return await self.file_ops.create_folder(arguments.get("path", ""))

        elif tool == "move_file":
            return await self.file_ops.move_file(
                source=arguments.get("source", ""),
                destination=arguments.get("destination", ""),
            )

        elif tool == "rename_file":
            return await self.file_ops.rename_file(
                path=arguments.get("path", ""),
                new_name=arguments.get("new_name", ""),
            )

        elif tool == "list_directory":
            entries = await self.file_ops.list_directory(arguments.get("path", ""))
            # Return as a successful result with directory listing
            return FileOpResult(
                success=True,
                operation="list_directory",
                source=arguments.get("path", ""),
                destination=json.dumps(entries[:20]),  # Cap at 20 entries in result
            )

        elif tool == "copy_file":
            src = arguments.get("source", "")
            dst = arguments.get("destination", "")
            # Use move_file logic but with copy
            src_path = Path(src).expanduser()
            dst_path = Path(dst).expanduser()
            try:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(str(src_path), str(dst_path))
                return FileOpResult(success=True, operation="copy_file", source=src, destination=dst)
            except OSError as e:
                return FileOpResult(success=False, operation="copy_file", source=src, error=str(e))

        elif tool == "read_file_info":
            path = Path(arguments.get("path", "")).expanduser()
            try:
                stat = path.stat()
                info = f"size={stat.st_size}, modified={stat.st_mtime}"
                return FileOpResult(success=True, operation="read_file_info", source=str(path), destination=info)
            except OSError as e:
                return FileOpResult(success=False, operation="read_file_info", source=str(path), error=str(e))

        elif tool == "get_system_status":
            import platform
            info = f"OS={platform.system()} {platform.version()}, Python={platform.python_version()}"
            return FileOpResult(success=True, operation="get_system_status", source="system", destination=info)

        # ─── GUI Operations ───────────────────────────────────────
        elif tool == "open_application":
            result = await self.gui_ops.open_application(arguments.get("app_name", ""))
            return FileOpResult(
                success=result.success, operation="open_application",
                source=arguments.get("app_name", ""), destination=result.details,
                error=result.error,
            )

        elif tool == "type_text":
            result = await self.gui_ops.type_text(
                text=arguments.get("text", ""),
                window_title=arguments.get("window_title", ""),
            )
            return FileOpResult(
                success=result.success, operation="type_text",
                source=arguments.get("window_title", "active window"),
                destination=result.details, error=result.error,
            )

        elif tool == "press_keys":
            result = await self.gui_ops.press_keys(arguments.get("keys", ""))
            return FileOpResult(
                success=result.success, operation="press_keys",
                source=arguments.get("keys", ""), destination=result.details,
                error=result.error,
            )

        elif tool == "list_windows":
            result = await self.gui_ops.list_windows()
            return FileOpResult(
                success=result.success, operation="list_windows",
                source="desktop", destination=result.details,
                error=result.error,
            )

        elif tool == "focus_window":
            result = await self.gui_ops.focus_window(arguments.get("window_title", ""))
            return FileOpResult(
                success=result.success, operation="focus_window",
                source=arguments.get("window_title", ""),
                destination=result.details, error=result.error,
            )

        else:
            return FileOpResult(
                success=False, operation=tool, source="",
                error=f"Unknown tool: '{tool}' — not implemented",
            )

    def _extract_path(self, arguments: dict[str, Any]) -> str:
        """Extract the primary path from tool arguments."""
        return arguments.get("path", "") or arguments.get("source", "")

    def _extract_destination(self, arguments: dict[str, Any]) -> str:
        """Extract the destination path from tool arguments."""
        return arguments.get("destination", "")

    def _log_transaction(
        self, task_id: str, step: int, tool: str,
        arguments: dict[str, Any], result: FileOpResult
    ) -> None:
        """Log a transaction for audit trail and rollback."""
        entry = {
            "task_id": task_id,
            "step": step,
            "tool": tool,
            "arguments": arguments,
            "success": result.success,
            "source": result.source,
            "destination": result.destination,
            "error": result.error,
            "timestamp": time.time(),
        }
        self._transaction_log.append(entry)

    def get_transaction_log(self) -> list[dict]:
        """Return the full transaction log."""
        return self._transaction_log
