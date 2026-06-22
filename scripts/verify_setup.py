#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
MACAL Agent System — Pre-Flight Verification
═══════════════════════════════════════════════════════════════

Run this script BEFORE starting development to verify all
prerequisites are installed and configured correctly.

Usage:
    python scripts/verify_setup.py

Exit codes:
    0 = All checks passed
    1 = One or more checks failed
═══════════════════════════════════════════════════════════════
"""

import sys
import os
import shutil
import platform
import subprocess
from pathlib import Path

# ─── Results tracking ─────────────────────────────────────────

checks_passed = 0
checks_failed = 0
checks_warned = 0


def check_pass(name: str, detail: str = ""):
    global checks_passed
    checks_passed += 1
    suffix = f" ({detail})" if detail else ""
    print(f"  \033[92m✅ PASS\033[0m  {name}{suffix}")


def check_fail(name: str, fix: str = ""):
    global checks_failed
    checks_failed += 1
    print(f"  \033[91m❌ FAIL\033[0m  {name}")
    if fix:
        print(f"           → FIX: {fix}")


def check_warn(name: str, note: str = ""):
    global checks_warned
    checks_warned += 1
    print(f"  \033[93m⚠️  WARN\033[0m  {name}")
    if note:
        print(f"           → {note}")


def run_cmd(cmd: str, timeout: int = 10) -> tuple:
    """Run a shell command and return (success, stdout)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return (result.returncode == 0, result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return (False, "")


# ─── Check Functions ──────────────────────────────────────────


def check_operating_system():
    """Verify Windows 11 is running."""
    print("\n── Operating System ──")
    if platform.system() != "Windows":
        check_fail(
            f"Windows required (detected: {platform.system()})",
            "This agent is designed for Windows 11"
        )
        return

    version = platform.version()
    build = int(version.split(".")[2]) if len(version.split(".")) >= 3 else 0

    if build >= 22000:
        check_pass("Windows 11 detected", f"Build {build}")
    elif build >= 10240:
        check_warn(
            f"Windows 10 detected (Build {build})",
            "Windows 11 recommended; most features still work on 10"
        )
    else:
        check_fail("Windows 11 required", f"Detected build: {build}")


def check_python():
    """Verify Python 3.11+."""
    print("\n── Python ──")
    if sys.version_info >= (3, 11):
        check_pass(
            "Python version",
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
    elif sys.version_info >= (3, 10):
        check_warn(
            f"Python {sys.version_info.major}.{sys.version_info.minor} (3.11+ recommended)",
            "Most things work; upgrade when convenient"
        )
    else:
        check_fail(
            f"Python {sys.version_info.major}.{sys.version_info.minor} too old",
            "winget install Python.Python.3.11"
        )


def check_git():
    """Verify Git is installed."""
    print("\n── Git ──")
    success, output = run_cmd("git --version")
    if success:
        check_pass("Git installed", output)
    else:
        check_fail("Git not found", "winget install Git.Git")


def check_ollama():
    """Verify Ollama is installed and running with required models."""
    print("\n── Ollama (Local LLM Runtime) ──")

    # Check binary exists
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        check_fail("Ollama not installed", "winget install Ollama")
        return

    success, version = run_cmd("ollama --version")
    if success:
        check_pass("Ollama installed", version.strip())
    else:
        check_pass("Ollama binary found", ollama_path)

    # Check Ollama is running (API reachable)
    try:
        import urllib.request
        import json

        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = [m["name"] for m in data.get("models", [])]

            check_pass("Ollama server running", f"{len(models)} model(s) loaded")

            # Check for required models
            has_primary = any("qwen3" in m and "8b" in m for m in models)
            has_fast = any("qwen3" in m and "0.8" in m for m in models)

            if has_primary:
                check_pass("Primary model (qwen3:8b) available")
            else:
                check_fail(
                    "Primary model not found",
                    "ollama pull qwen3:8b"
                )

            if has_fast:
                check_pass("Fast model (qwen3:0.8b) available")
            else:
                check_warn(
                    "Fast model (qwen3:0.8b) not found",
                    "Optional but recommended: ollama pull qwen3:0.8b"
                )

    except Exception:
        check_fail(
            "Ollama server not responding",
            "Start Ollama: open Ollama app or run 'ollama serve'"
        )


def check_docker():
    """Verify Docker is installed."""
    print("\n── Docker ──")
    success, output = run_cmd("docker --version")
    if success:
        check_pass("Docker installed", output)
    else:
        check_warn(
            "Docker not found",
            "Needed for n8n local testing. Install: docker.com/products/docker-desktop"
        )

    # Check Docker is running
    success, _ = run_cmd("docker info", timeout=15)
    if success:
        check_pass("Docker daemon running")
    else:
        check_warn(
            "Docker daemon not running",
            "Start Docker Desktop before using n8n locally"
        )


def check_nodejs():
    """Verify Node.js is installed (for Playwright MCP)."""
    print("\n── Node.js (for Playwright MCP) ──")
    success, output = run_cmd("node --version")
    if success:
        version = output.strip().lstrip("v")
        major = int(version.split(".")[0]) if version else 0
        if major >= 20:
            check_pass("Node.js installed", f"v{version}")
        else:
            check_warn(
                f"Node.js v{version} (v20+ recommended)",
                "winget install OpenJS.NodeJS.LTS"
            )
    else:
        check_warn(
            "Node.js not found",
            "Needed for Phase 3+ (Playwright MCP). Install: winget install OpenJS.NodeJS.LTS"
        )


def check_hardware():
    """Check RAM and disk space."""
    print("\n── Hardware ──")

    # RAM check (Windows-specific)
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        mem = MEMORYSTATUSEX(dwLength=ctypes.sizeof(MEMORYSTATUSEX))
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
        total_gb = mem.ullTotalPhys / (1024 ** 3)
        avail_gb = mem.ullAvailPhys / (1024 ** 3)

        if total_gb >= 16:
            check_pass(f"RAM: {total_gb:.0f} GB total, {avail_gb:.1f} GB available")
        elif total_gb >= 8:
            check_warn(
                f"RAM: {total_gb:.0f} GB (16 GB recommended for qwen3:8b)",
                "Use qwen3:4b model if inference is too slow"
            )
        else:
            check_fail(
                f"RAM: {total_gb:.0f} GB (minimum 8 GB required)",
                "Consider upgrading RAM or using qwen3:0.8b only"
            )
    except (AttributeError, OSError):
        check_warn("Could not detect RAM", "Verify manually: 16 GB recommended")

    # Disk space
    try:
        usage = shutil.disk_usage("C:\\")
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)

        if free_gb >= 30:
            check_pass(f"Disk: {free_gb:.0f} GB free of {total_gb:.0f} GB")
        elif free_gb >= 15:
            check_warn(
                f"Disk: {free_gb:.0f} GB free (30 GB recommended)",
                "Models + data need space. Free up disk if possible."
            )
        else:
            check_fail(
                f"Disk: only {free_gb:.0f} GB free",
                "Need 30+ GB for models, logs, and organized files"
            )
    except OSError:
        check_warn("Could not check disk space", "Verify manually: 30+ GB free recommended")


def check_gpu():
    """Check for NVIDIA GPU (optional but speeds up inference)."""
    print("\n── GPU (Optional — speeds up LLM inference) ──")

    success, output = run_cmd("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits")
    if success and output:
        lines = output.strip().split("\n")
        for line in lines:
            parts = line.split(",")
            name = parts[0].strip() if len(parts) > 0 else "Unknown"
            vram = parts[1].strip() if len(parts) > 1 else "?"
            vram_gb = int(vram) / 1024 if vram.isdigit() else 0

            if vram_gb >= 8:
                check_pass(f"GPU: {name} ({vram_gb:.0f} GB VRAM) — excellent for 8B models")
            elif vram_gb >= 6:
                check_pass(f"GPU: {name} ({vram_gb:.0f} GB VRAM) — good for 8B quantized")
            elif vram_gb >= 4:
                check_warn(
                    f"GPU: {name} ({vram_gb:.0f} GB VRAM)",
                    "Limited VRAM — use 4B model or CPU offloading"
                )
            else:
                check_warn(f"GPU: {name} ({vram_gb:.0f} GB VRAM) — too small for LLM, will use CPU")
    else:
        check_warn(
            "No NVIDIA GPU detected (or nvidia-smi not in PATH)",
            "CPU inference works fine — just slower (8-15 tok/s vs 40-60 with GPU)"
        )


def check_network():
    """Check if Hetzner server is reachable (optional)."""
    print("\n── Network (Hetzner Connectivity) ──")

    # Check basic internet
    try:
        import urllib.request
        urllib.request.urlopen("https://example.com", timeout=5)
        check_pass("Internet connectivity")
    except Exception:
        check_warn("No internet detected", "Needed for initial setup only; agent works offline after")

    # Check Hetzner SSH (non-blocking check via TCP)
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("77.42.43.250", 22))
        sock.close()
        if result == 0:
            check_pass("Hetzner server reachable (SSH port 22 open)")
        else:
            check_warn(
                "Hetzner server not reachable on port 22",
                "Verify: ssh root@77.42.43.250 (may be blocked from this network)"
            )
    except Exception:
        check_warn("Could not test Hetzner connectivity", "Test manually: ssh root@77.42.43.250")


def check_project_structure():
    """Verify project directories exist."""
    print("\n── Project Structure ──")

    required_dirs = [
        "src/daemon",
        "src/intelligence",
        "src/execution",
        "src/security",
        "src/file_organizer",
        "config",
        "scripts",
        "logs",
        "data",
        "tests",
        "docs",
        "n8n_workflows",
    ]

    # Find project root (where this script lives is scripts/, go up one)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    missing = []
    for d in required_dirs:
        if not (project_root / d).is_dir():
            missing.append(d)

    if not missing:
        check_pass(f"All {len(required_dirs)} project directories present")
    else:
        check_fail(
            f"Missing directories: {', '.join(missing)}",
            "Run project setup or create manually"
        )

    # Check config file
    if (project_root / "config" / "agent.yaml").is_file():
        check_pass("config/agent.yaml exists")
    else:
        check_fail("config/agent.yaml missing", "Create from template in IMPLEMENTATION_ROADMAP.md")


# ─── Main ─────────────────────────────────────────────────────


def main():
    print("\n" + "═" * 60)
    print("  MACAL Agent System — Pre-Flight Verification")
    print("═" * 60)

    check_operating_system()
    check_python()
    check_git()
    check_ollama()
    check_docker()
    check_nodejs()
    check_hardware()
    check_gpu()
    check_network()
    check_project_structure()

    # ─── Summary ──────────────────────────────────────────────
    print("\n" + "═" * 60)
    total = checks_passed + checks_failed + checks_warned
    print(f"  Results: {checks_passed} passed, {checks_failed} failed, {checks_warned} warnings")
    print(f"  Total checks: {total}")
    print("═" * 60)

    if checks_failed == 0:
        print("\n  \033[92m🎉 ALL CRITICAL CHECKS PASSED\033[0m")
        print("  You are ready to begin Phase 1: Foundation Layer!")
        if checks_warned > 0:
            print(f"  ({checks_warned} non-critical warnings — address when convenient)")
        print()
        return 0
    else:
        print(f"\n  \033[91m⛔ {checks_failed} CRITICAL CHECK(S) FAILED\033[0m")
        print("  Fix the issues marked ❌ above before proceeding.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
