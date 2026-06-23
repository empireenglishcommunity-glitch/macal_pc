"""
MACAL Agent Bridge - Secure command execution with human approval.

This script:
1. Reads commands from commands.json (pushed by AI via GitHub)
2. Displays each command with risk level and explanation
3. Asks for your approval before executing
4. Captures output and saves to results.json
5. You push results back (or auto-push if configured)

Usage:
    cd C:\\Users\\97150\\macal_pc
    python bridge/bridge.py

Commands are color-coded by risk:
    GREEN  = safe (read-only, info gathering)
    YELLOW = moderate (creates/modifies files)
    RED    = needs careful review (system changes)

Security:
    - EVERY command requires explicit approval
    - Dangerous patterns are auto-blocked
    - All output is captured and logged
    - Timeout prevents hanging commands
"""
import json
import subprocess
import sys
import os
import time
from pathlib import Path

# Configuration
BRIDGE_DIR = Path(__file__).parent
COMMANDS_FILE = BRIDGE_DIR / "commands.json"
RESULTS_FILE = BRIDGE_DIR / "results.json"
HISTORY_FILE = BRIDGE_DIR / "history.log"
TIMEOUT = 120  # seconds per command
PROJECT_DIR = Path("C:/Users/97150/macal_pc")

# Dangerous patterns that are always blocked
BLOCKED_PATTERNS = [
    "rm -rf /", "del /s /q C:\\", "format ", "fdisk",
    "Remove-Item -Recurse -Force C:\\", "reg delete",
    "bcdedit", "diskpart", "cipher /w",
    "shutdown", "taskkill /f /im explorer",
]


def load_commands():
    """Load command batch from commands.json."""
    if not COMMANDS_FILE.exists():
        print("  No commands.json found. Waiting for commands...")
        return None
    try:
        with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data.get("commands"):
            print("  No commands in queue.")
            return None
        return data
    except json.JSONDecodeError as e:
        print(f"  Error reading commands.json: {e}")
        return None


def is_blocked(command):
    """Check if command matches a dangerous pattern."""
    cmd_lower = command.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in cmd_lower:
            return True
    return False


def display_command(cmd, index, total):
    """Display a command with its metadata."""
    risk = cmd.get("risk", "yellow").upper()
    risk_icon = {"GREEN": "[SAFE]", "YELLOW": "[MODERATE]", "RED": "[CAREFUL]"}.get(risk, "[?]")
    print(f"\n  {'='*60}")
    print(f"  Command {index}/{total}  {risk_icon} {risk}")
    print(f"  {'='*60}")
    print(f"  Description: {cmd.get('description', 'No description')}")
    print(f"  Command:     {cmd.get('command', '')}")
    print(f"  {'-'*60}")


def get_approval(batch_mode=False):
    """Ask user for approval."""
    if batch_mode:
        return True
    while True:
        choice = input("  Execute? [Y]es / [N]o / [A]ll remaining / [Q]uit: ").strip().upper()
        if choice in ("Y", "YES"):
            return "yes"
        elif choice in ("N", "NO"):
            return "no"
        elif choice in ("A", "ALL"):
            return "all"
        elif choice in ("Q", "QUIT"):
            return "quit"
        else:
            print("  Please enter Y, N, A, or Q")


def execute_command(command, cwd=None):
    """Execute a command and capture output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            cwd=cwd or str(PROJECT_DIR),
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "TIMEOUT after " + str(TIMEOUT) + "s", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


def save_results(batch_id, results):
    """Save execution results to results.json."""
    output = {
        "batch_id": batch_id,
        "executed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": results,
    }
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {RESULTS_FILE}")


def log_history(batch_id, results):
    """Append to history log."""
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Batch: {batch_id} | Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        for r in results:
            status = "OK" if r["success"] else "FAIL"
            f.write(f"  [{status}] {r['command']}\n")
            if r.get("stdout"):
                f.write(f"    stdout: {r['stdout'][:200]}\n")
            if r.get("stderr"):
                f.write(f"    stderr: {r['stderr'][:200]}\n")


def clear_commands():
    """Clear the command queue after execution."""
    with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump({"batch_id": None, "description": "Queue empty - waiting for next batch", "commands": []}, f, indent=2)


def main():
    print("\n" + "=" * 60)
    print("  MACAL AGENT BRIDGE v1.0")
    print("  Secure command execution with human approval")
    print("=" * 60)

    # Load commands
    data = load_commands()
    if not data:
        return

    batch_id = data.get("batch_id", "unknown")
    description = data.get("description", "")
    commands = data.get("commands", [])

    print(f"\n  Batch: {batch_id}")
    print(f"  Description: {description}")
    print(f"  Commands: {len(commands)}")

    # Process commands
    results = []
    approve_all = False

    for i, cmd in enumerate(commands, 1):
        command_str = cmd.get("command", "")

        # Security check
        if is_blocked(command_str):
            print(f"\n  BLOCKED (dangerous pattern): {command_str}")
            results.append({
                "id": cmd.get("id", i),
                "command": command_str,
                "success": False,
                "stdout": "",
                "stderr": "BLOCKED by security filter",
                "approved": False,
            })
            continue

        display_command(cmd, i, len(commands))

        # Get approval
        if not approve_all:
            approval = get_approval()
            if approval == "quit":
                print("\n  Aborted by user.")
                break
            elif approval == "no":
                results.append({
                    "id": cmd.get("id", i),
                    "command": command_str,
                    "success": False,
                    "stdout": "",
                    "stderr": "Skipped by user",
                    "approved": False,
                })
                continue
            elif approval == "all":
                approve_all = True

        # Execute
        print(f"  Executing...")
        result = execute_command(command_str)
        result["id"] = cmd.get("id", i)
        result["command"] = command_str
        result["approved"] = True
        results.append(result)

        # Display result
        if result["success"]:
            print(f"  Result: OK")
            if result["stdout"]:
                # Show first 5 lines of output
                lines = result["stdout"].split("\n")[:5]
                for line in lines:
                    print(f"    {line}")
                if len(result["stdout"].split("\n")) > 5:
                    print(f"    ... ({len(result['stdout'].split(chr(10)))} lines total)")
        else:
            print(f"  Result: FAILED")
            if result["stderr"]:
                print(f"    Error: {result['stderr'][:200]}")

    # Save results
    if results:
        save_results(batch_id, results)
        log_history(batch_id, results)
        clear_commands()

    print(f"\n  Done! {sum(1 for r in results if r.get('success'))} succeeded, "
          f"{sum(1 for r in results if not r.get('success'))} failed/skipped")
    print(f"\n  Next step: run 'git add bridge/results.json && git commit -m \"results\" && git push'")
    print(f"  Or I can read the results when you tell me they're ready.\n")


if __name__ == "__main__":
    os.chdir(str(PROJECT_DIR))
    main()
