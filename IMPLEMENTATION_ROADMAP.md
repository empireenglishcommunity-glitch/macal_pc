# Implementation Roadmap: Professional-Grade AI Desktop Agent

## Project: MACAL Agent System
## Version: 1.0
## Date: June 22, 2026
## Author: Systems Architecture Division

---

## Table of Contents

1. [Project Vision & Strategy](#1-project-vision--strategy)
2. [System Architecture](#2-system-architecture)
3. [Development Phases](#3-development-phases)
4. [Phase 0: Pre-Development Preparation](#4-phase-0-pre-development-preparation)
5. [Phase 1: Foundation Layer](#5-phase-1-foundation-layer)
6. [Phase 2: Agent Intelligence](#6-phase-2-agent-intelligence)
7. [Phase 3: Windows Desktop Control](#7-phase-3-windows-desktop-control)
8. [Phase 4: Orchestration & Remote Control](#8-phase-4-orchestration--remote-control)
9. [Phase 5: File Intelligence System](#9-phase-5-file-intelligence-system)
10. [Phase 6: Security & Hardening](#10-phase-6-security--hardening)
11. [Phase 7: Production Deployment](#11-phase-7-production-deployment)
12. [Phase 8: Advanced Capabilities](#12-phase-8-advanced-capabilities)
13. [Professional-Grade Requirements](#13-professional-grade-requirements)
14. [Risk Register & Mitigation](#14-risk-register--mitigation)
15. [Success Metrics](#15-success-metrics)
16. [Maintenance & Evolution](#16-maintenance--evolution)

---


## 1. Project Vision & Strategy

### 1.1 Vision Statement

Build a self-hosted, zero-vendor-lock-in AI agent system that controls,
manages, and organizes a Windows 11 desktop environment through natural
language — powered entirely by local LLM inference and orchestrated
through existing infrastructure.

### 1.2 Strategic Principles

| # | Principle | Implication |
|---|-----------|------------|
| 1 | **Zero new recurring cost** | Use existing Hetzner server + local hardware only |
| 2 | **Own everything** | MIT/Apache/BSD licensed tools; all data stays local |
| 3 | **5-year viability** | No tool that could disappear or paywall in 2 years |
| 4 | **Incremental value** | Each phase delivers usable capability independently |
| 5 | **Fail gracefully** | Every component can degrade without breaking others |
| 6 | **Human-in-the-loop** | No destructive action without explicit approval |
| 7 | **Observable** | Every action logged, every decision traceable |
| 8 | **Scalable by design** | Architecture supports 10x task volume without redesign |

### 1.3 Existing Infrastructure (Already Paid, Already Running)

| Asset | Status | Role in Agent System |
|-------|:------:|---------------------|
| Hetzner CX23 (4GB, Helsinki) | ✅ Live | Orchestration, scheduling, remote trigger |
| n8n (Docker, v2.26.8) | ✅ Live | Workflow engine, webhook receiver |
| Cloudflare Tunnel | ✅ Live | Secure public access, no open ports |
| Telegram monitoring bot | ✅ Live | Alerts, notifications, command interface |
| Windows 11 PC | ✅ Available | LLM inference, desktop execution, file management |
| Domain (empireenglish.online) | ✅ Active | Subdomain routing for agent API |

### 1.4 Target Capabilities (End State)

When fully implemented, the system will:

```
✅ Organize files intelligently based on content analysis
✅ Control any Windows application via natural language
✅ Execute multi-step workflows across applications
✅ Schedule recurring automation tasks
✅ Accept commands from Telegram (anywhere, any device)
✅ Accept commands from n8n web UI (from any browser)
✅ Maintain full audit trail with one-click rollback
✅ Self-monitor and report health status
✅ Handle errors gracefully with retry logic
✅ Operate 100% offline (LLM runs locally)
✅ Secure all communications (encrypted mesh network)
✅ Approve/reject destructive actions before execution
```

---


## 2. System Architecture

### 2.1 High-Level Architecture Diagram

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    MACAL AGENT SYSTEM — ARCHITECTURE                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  ┌─────────────────────────────────────────────────────────────────┐ ║
║  │              TRIGGER LAYER (How tasks enter the system)          │ ║
║  │                                                                  │ ║
║  │  [Telegram Bot]  [n8n Web UI]  [Cron Schedule]  [File Watcher]  │ ║
║  │  [Hotkey AHK]    [CLI Direct]  [Webhook API]   [Voice Input*]  │ ║
║  └─────────────────────────────┬───────────────────────────────────┘ ║
║                                │                                      ║
║  ┌─────────────────────────────┴───────────────────────────────────┐ ║
║  │         ORCHESTRATION LAYER (Hetzner Server — Always On)         │ ║
║  │                                                                  │ ║
║  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │ ║
║  │  │   n8n    │  │  Task    │  │  Audit   │  │  Notification│   │ ║
║  │  │ Workflow │  │  Queue   │  │   Log    │  │  Engine      │   │ ║
║  │  │ Engine   │  │ (Redis)  │  │ (SQLite) │  │ (Telegram)   │   │ ║
║  │  └─────┬────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │ ║
║  │        └─────────────┼─────────────┼────────────────┘           │ ║
║  └──────────────────────┼─────────────┼───────────────────────────┘ ║
║                         │  Tailscale  │                              ║
║                         │  Encrypted  │                              ║
║  ┌──────────────────────┼─────────────┼───────────────────────────┐ ║
║  │      INTELLIGENCE LAYER (Windows PC — Local LLM Inference)      │ ║
║  │                      │             │                             │ ║
║  │  ┌──────────────────┐│  ┌─────────┴──────────────────────────┐ │ ║
║  │  │  Agent Daemon    ││  │         Ollama Runtime              │ │ ║
║  │  │  (Python service)││  │  Qwen3-8B (primary reasoning)      │ │ ║
║  │  │  - Receives tasks││  │  Qwen3-VL (screenshot analysis*)   │ │ ║
║  │  │  - Routes to exec││  │  Qwen3-0.8B (fast classification)  │ │ ║
║  │  │  - Reports back  ││  │                                    │ │ ║
║  │  └────────┬─────────┘│  └────────────────────────────────────┘ │ ║
║  │           │           │                                          │ ║
║  └───────────┼───────────┼──────────────────────────────────────────┘ ║
║              │           │                                            ║
║  ┌───────────┼───────────┼──────────────────────────────────────────┐ ║
║  │     EXECUTION LAYER (Windows PC — Actions on the Desktop)        │ ║
║  │           │           │                                           │ ║
║  │  ┌───────┴───────────┴──────────────────────────────────────┐   │ ║
║  │  │              Permission Guard (security gate)             │   │ ║
║  │  │  - Classifies action (green/yellow/red/black)            │   │ ║
║  │  │  - Enforces path allowlists                              │   │ ║
║  │  │  - Requires approval for destructive ops                 │   │ ║
║  │  │  - Logs everything to transaction journal                │   │ ║
║  │  └──────────┬──────────────────────────────────┬────────────┘   │ ║
║  │             │                                   │                │ ║
║  │  ┌──────────┴──────────┐        ┌─────────────┴────────────┐   │ ║
║  │  │  FILE OPERATIONS    │        │  GUI OPERATIONS           │   │ ║
║  │  │  - Open Interpreter │        │  - Microsoft UFO3         │   │ ║
║  │  │  - Python shutil    │        │  - agent-desktop CLI      │   │ ║
║  │  │  - watchdog pipeline│        │  - pywinauto             │   │ ║
║  │  │  - MCP filesystem   │        │  - AutoHotkey macros     │   │ ║
║  │  └─────────────────────┘        │  - Playwright MCP        │   │ ║
║  │                                  └──────────────────────────┘   │ ║
║  └──────────────────────────────────────────────────────────────────┘ ║
║                                                                       ║
║  ┌──────────────────────────────────────────────────────────────────┐ ║
║  │          PERSISTENCE LAYER (Data Storage & Recovery)              │ ║
║  │                                                                   │ ║
║  │  [Transaction Journal]  [Audit Log]  [Task History]  [Rollback]  │ ║
║  │  (SQLite on PC)         (SQLite)     (n8n DB)       (PC local)   │ ║
║  └──────────────────────────────────────────────────────────────────┘ ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 2.2 Communication Flow

```
SCENARIO: User sends "Organize my Downloads" via Telegram

1. [Telegram] → message arrives
2. [Hetzner/n8n] → webhook receives message
3. [Hetzner/n8n] → validates sender (is it the admin?)
4. [Hetzner/n8n] → queues task → sends to PC via Tailscale HTTP
5. [PC/Agent Daemon] → receives task JSON
6. [PC/Ollama] → Qwen3-8B plans execution steps
7. [PC/Permission Guard] → validates all planned file operations
8. [PC/Execution Layer] → performs file moves/renames
9. [PC/Agent Daemon] → sends result back to Hetzner
10. [Hetzner/n8n] → logs result → notifies via Telegram
11. [Telegram] → user sees: "✅ Organized 47 files into 6 folders"
```

### 2.3 Component Dependency Map

```
                    Ollama (foundation — everything depends on this)
                         │
            ┌────────────┼────────────┐
            │            │            │
         UFO3    Open Interpreter  Agent Scripts
            │            │            │
            └────────────┼────────────┘
                         │
                  Permission Guard
                         │
                  Agent Daemon
                         │
                    Tailscale
                         │
                  Hetzner / n8n
                         │
              Telegram / Web UI / API
```

**Build order follows dependencies bottom-up:**
Ollama → Execution tools → Permission Guard → Agent Daemon → Networking → Orchestration → Triggers

---


## 3. Development Phases

### 3.1 Phase Overview & Timeline

```
PHASE 0: Pre-Development Preparation ──── Days 1-2 (weekend)
    │    Hardware audit, software installs, repository setup
    │
PHASE 1: Foundation Layer ─────────────── Days 3-5
    │    Ollama + models, Python environment, basic agent test
    │
PHASE 2: Agent Intelligence ───────────── Days 6-10
    │    Agent Daemon, Ollama integration, tool-use pipeline
    │
PHASE 3: Windows Desktop Control ──────── Days 11-16
    │    UFO3, agent-desktop, pywinauto, GUI automation
    │
PHASE 4: Orchestration & Remote ───────── Days 17-22
    │    Tailscale, Hetzner n8n workflows, Telegram commands
    │
PHASE 5: File Intelligence ────────────── Days 23-28
    │    AI classification, watchdog pipeline, rollback system
    │
PHASE 6: Security & Hardening ─────────── Days 29-33
    │    Permission Guard, audit system, safety testing
    │
PHASE 7: Production Deployment ─────────── Days 34-38
    │    Integration testing, monitoring, documentation
    │
PHASE 8: Advanced Capabilities ─────────── Days 39+ (ongoing)
         Multi-app workflows, voice, learning, expansion
```

### 3.2 Key Milestones

| Milestone | Phase | Definition of Done |
|-----------|:-----:|-------------------|
| **M1: First Word** | 1 | Ollama responds to a prompt locally |
| **M2: First Action** | 2 | Agent creates a folder from natural language |
| **M3: First GUI Click** | 3 | Agent opens Notepad and types text |
| **M4: First Remote Trigger** | 4 | Telegram message triggers action on PC |
| **M5: First Smart Organization** | 5 | Agent classifies and moves 10 files correctly |
| **M6: First Secure Execution** | 6 | Destructive action blocked, logged, and reported |
| **M7: Production Ready** | 7 | System runs unattended for 72 hours without failure |
| **M8: Advanced Flow** | 8 | Multi-app workflow (e.g., download → rename → file → notify) |

### 3.3 Development Principles

| Principle | Practice |
|-----------|---------|
| **Test each layer before building next** | Don't start Phase 3 until Phase 2's milestone passes |
| **One working path first** | Get end-to-end working with ONE tool, then add alternatives |
| **Configuration over code** | Use config files, not hardcoded values |
| **Log everything from day 1** | Even prototype code should log actions |
| **Version control always** | Every script, config, and workflow in Git |
| **Document decisions** | Write WHY you chose X over Y (future-you will thank you) |

---


## 4. Phase 0: Pre-Development Preparation

**Duration:** 1-2 days (weekend prep)
**Goal:** Verify all hardware, install prerequisites, create project structure

### 4.1 Hardware Audit Checklist

```
□ Windows 11 version: Confirm 24H2 or later
□ RAM: Minimum 16 GB (for Qwen3-8B + system + tools)
    → If 8 GB only: plan for Qwen3-4B model instead
□ GPU: Check if NVIDIA GPU present
    → If yes: note VRAM (6GB+ enables fast inference)
    → If no: CPU inference works (slower, still viable)
□ Disk: Confirm 30+ GB free for models + tools + data
□ Network: Confirm internet access for initial downloads
□ SSH to Hetzner: Verify ssh root@77.42.43.250 works
```

### 4.2 Software Prerequisites (Install Before Starting)

| Software | Purpose | Install Command | Verify |
|----------|---------|----------------|--------|
| Python 3.11+ | Agent scripts, tools | `winget install Python.Python.3.11` | `python --version` |
| Git | Version control | `winget install Git.Git` | `git --version` |
| Docker Desktop | n8n local testing, containers | Download from docker.com | `docker --version` |
| Ollama | Local LLM runtime | `winget install Ollama` | `ollama --version` |
| Node.js 20+ | Playwright MCP, some tools | `winget install OpenJS.NodeJS.LTS` | `node --version` |
| Rust toolchain | agent-desktop (if building from source) | rustup.rs installer | `cargo --version` |
| VS Code | Development (optional) | `winget install Microsoft.VisualStudioCode` | — |

### 4.3 Repository Structure (Create This)

```bash
# Create the project directory structure
mkdir -p C:\Projects\macal-agent
cd C:\Projects\macal-agent

# Initialize Git
git init

# Create directory structure
mkdir -p src\daemon          # Agent daemon (receives + routes tasks)
mkdir -p src\intelligence    # LLM integration, prompt engineering
mkdir -p src\execution       # File ops, GUI ops, shell ops
mkdir -p src\security        # Permission guard, audit log
mkdir -p src\file_organizer  # AI file classification + pipeline
mkdir -p config              # All configuration files
mkdir -p scripts             # Utility scripts (setup, deploy, test)
mkdir -p logs                # Runtime logs (gitignored)
mkdir -p data                # SQLite databases, state files
mkdir -p tests               # Test scripts and fixtures
mkdir -p docs                # Architecture docs, decision log
mkdir -p n8n_workflows       # Exported n8n workflow JSONs
```

### 4.4 Project Configuration Files

**`config/agent.yaml` (master config):**
```yaml
# MACAL Agent System — Master Configuration
version: "1.0"

ollama:
  host: "http://localhost:11434"
  primary_model: "qwen3:8b"
  fast_model: "qwen3:0.8b"       # For quick classification
  vision_model: "qwen3-vl:8b"   # For screenshot analysis (Phase 8)
  timeout_seconds: 120

agent_daemon:
  host: "0.0.0.0"
  port: 8900
  allowed_origins:
    - "100.0.0.0/8"              # Tailscale network only

security:
  mode: "approval"               # "auto", "approval", "staging"
  allowed_write_paths:
    - "~/Organized"
    - "~/AgentWork"
    - "~/Downloads"
    - "~/Documents/Agent-Managed"
  blocked_paths:
    - "C:/Windows"
    - "C:/Program Files"
    - "C:/Program Files (x86)"
    - "~/AppData"
    - "~/.ssh"
  max_files_per_operation: 100
  require_approval_for:
    - "delete"
    - "overwrite"
    - "admin"
    - "install"

hetzner:
  tailscale_ip: "100.x.y.z"     # Fill after Tailscale setup
  n8n_webhook_base: "https://bot.empireenglish.online"

notifications:
  telegram_enabled: true
  telegram_chat_id: ""           # Your admin chat ID
  notify_on: ["task_complete", "task_failed", "approval_needed"]

logging:
  level: "INFO"
  file: "logs/agent.log"
  max_size_mb: 50
  rotation: 7                    # Keep 7 days
  audit_db: "data/audit.db"
```

### 4.5 Pre-Flight Verification Script

**`scripts/verify_setup.py`:**
```python
"""Run this BEFORE starting development to verify all prerequisites."""
import subprocess, sys, shutil, platform, os
from pathlib import Path

checks = []

def check(name, condition, fix=""):
    status = "✅" if condition else "❌"
    checks.append((status, name, fix))
    print(f"  {status} {name}" + (f" → FIX: {fix}" if not condition and fix else ""))

print("\n=== MACAL Agent System — Pre-Flight Check ===\n")

# OS
check("Windows 11", platform.system() == "Windows" and int(platform.version().split('.')[2]) >= 22000,
      "This system requires Windows 11")

# Python
check("Python 3.11+", sys.version_info >= (3, 11),
      "winget install Python.Python.3.11")

# Git
check("Git installed", shutil.which("git") is not None,
      "winget install Git.Git")

# Ollama
check("Ollama installed", shutil.which("ollama") is not None,
      "winget install Ollama")

# Ollama running
try:
    import requests
    r = requests.get("http://localhost:11434/api/tags", timeout=3)
    check("Ollama running", r.status_code == 200)
except:
    check("Ollama running", False, "Start Ollama: ollama serve")

# Model available
try:
    r = requests.get("http://localhost:11434/api/tags", timeout=3)
    models = [m["name"] for m in r.json().get("models", [])]
    check("Qwen3-8B model", any("qwen3" in m for m in models),
          "ollama pull qwen3:8b")
except:
    check("Qwen3-8B model", False, "ollama pull qwen3:8b")

# Docker
check("Docker installed", shutil.which("docker") is not None,
      "Install Docker Desktop from docker.com")

# Node.js
check("Node.js 20+", shutil.which("node") is not None,
      "winget install OpenJS.NodeJS.LTS")

# Disk space
free_gb = shutil.disk_usage("C:\\").free / (1024**3)
check(f"Disk space ({free_gb:.1f} GB free)", free_gb >= 30,
      "Need 30+ GB free for models and data")

# RAM
import ctypes
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
mem = MEMORYSTATUSEX(dwLength=ctypes.sizeof(MEMORYSTATUSEX))
ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
total_gb = mem.ullTotalPhys / (1024**3)
check(f"RAM ({total_gb:.0f} GB total)", total_gb >= 16,
      "16 GB recommended; 8 GB works with smaller models")

# SSH to Hetzner (optional check)
print("\n  ℹ️  Hetzner SSH: test manually with 'ssh root@77.42.43.250'")

# Summary
print(f"\n{'='*50}")
passed = sum(1 for s, _, _ in checks if s == "✅")
total = len(checks)
print(f"  Result: {passed}/{total} checks passed")
if passed == total:
    print("  🎉 All prerequisites met — ready to begin Phase 1!")
else:
    print("  ⚠️  Fix the issues above before proceeding.")
print()
```

### 4.6 Phase 0 Completion Criteria

```
□ All prerequisites installed and verified
□ Repository created with correct structure
□ Configuration file template in place
□ Pre-flight script passes all checks
□ SSH to Hetzner confirmed working
□ Ollama installed and responds to prompts
□ At least one model pulled (qwen3:8b)
□ Git repository initialized with first commit
```

---


## 5. Phase 1: Foundation Layer

**Duration:** 3 days
**Goal:** Ollama serving models + basic Python agent can call LLM and get structured responses
**Milestone:** M1 — Ollama responds to a prompt with valid JSON tool-use output

### 5.1 Tasks

| # | Task | Time | Priority |
|---|------|:----:|:--------:|
| 1.1 | Pull all required models via Ollama | 30 min | Critical |
| 1.2 | Create Python virtual environment | 5 min | Critical |
| 1.3 | Install core Python dependencies | 10 min | Critical |
| 1.4 | Build `OllamaClient` wrapper class | 2 hours | Critical |
| 1.5 | Build `StructuredOutput` parser (JSON mode) | 2 hours | Critical |
| 1.6 | Build `ToolRegistry` (function calling interface) | 3 hours | High |
| 1.7 | Test: send prompt → receive structured action plan | 1 hour | Critical |
| 1.8 | Benchmark: measure tokens/sec on your hardware | 30 min | Medium |
| 1.9 | Document: record actual performance numbers | 30 min | Medium |

### 5.2 Key Deliverables

**`src/intelligence/ollama_client.py`** — Wrapper for Ollama API:
- Send messages (chat completion format)
- Stream responses (optional, for long outputs)
- JSON mode (force structured output)
- Tool/function calling format
- Model switching (primary vs fast vs vision)
- Timeout handling and retry logic
- Token counting (estimate)

**`src/intelligence/tool_registry.py`** — Tool definition system:
- Define tools with name, description, parameters (JSON Schema)
- Register tools dynamically
- Parse LLM tool-call responses into executable commands
- Validate parameters against schema before execution

**`src/intelligence/prompts.py`** — System prompt templates:
- Agent system prompt (role, capabilities, rules)
- File organization prompt
- GUI automation prompt
- Classification prompt (fast model)

### 5.3 Verification Test

```python
# Phase 1 milestone test — must pass before Phase 2
from src.intelligence.ollama_client import OllamaClient
from src.intelligence.tool_registry import ToolRegistry

client = OllamaClient(model="qwen3:8b")
registry = ToolRegistry()
registry.register("create_folder", {"path": "string"}, "Create a folder")
registry.register("move_file", {"source": "string", "destination": "string"}, "Move a file")

response = client.chat_with_tools(
    message="Create a folder called 'Reports' in my Documents",
    tools=registry.get_tool_definitions()
)

# MUST produce a valid tool call:
assert response.tool_calls is not None
assert response.tool_calls[0].name == "create_folder"
assert "Reports" in response.tool_calls[0].arguments["path"]
print("✅ Phase 1 Milestone PASSED: LLM produces valid tool calls")
```

---

## 6. Phase 2: Agent Intelligence

**Duration:** 5 days
**Goal:** Agent Daemon that receives tasks, plans steps, executes them, and reports results
**Milestone:** M2 — Agent creates a folder from natural language instruction

### 6.1 Tasks

| # | Task | Time | Priority |
|---|------|:----:|:--------:|
| 2.1 | Build `AgentDaemon` HTTP server (FastAPI/Flask) | 3 hours | Critical |
| 2.2 | Build `TaskPlanner` (decomposes instruction → steps) | 4 hours | Critical |
| 2.3 | Build `ExecutionEngine` (executes steps sequentially) | 4 hours | Critical |
| 2.4 | Build `FileOperations` executor (create/move/rename/delete) | 3 hours | Critical |
| 2.5 | Build `ShellExecutor` (run commands safely) | 2 hours | High |
| 2.6 | Build `TransactionJournal` (log all ops for rollback) | 3 hours | Critical |
| 2.7 | Build `ResultReporter` (format results for notification) | 2 hours | High |
| 2.8 | Integration test: full task lifecycle | 3 hours | Critical |
| 2.9 | Error handling: graceful failure and partial rollback | 3 hours | High |
| 2.10 | API documentation (OpenAPI spec) | 1 hour | Medium |

### 6.2 Agent Daemon API Design

```
POST /api/v1/task
  Body: {"instruction": "...", "context": {...}, "priority": "normal"}
  Response: {"task_id": "uuid", "status": "queued"}

GET /api/v1/task/{task_id}
  Response: {"task_id": "...", "status": "completed|failed|running", "result": {...}}

POST /api/v1/task/{task_id}/approve
  Body: {"approved": true|false}
  Response: {"status": "executing|cancelled"}

GET /api/v1/health
  Response: {"status": "healthy", "ollama": "connected", "uptime": 3600}

POST /api/v1/rollback
  Body: {"task_id": "uuid"} OR {"last_n": 5}
  Response: {"rolled_back": 5, "details": [...]}
```

### 6.3 Task Execution Flow (Internal)

```python
# Simplified execution flow
async def execute_task(instruction: str) -> TaskResult:
    # 1. Plan
    plan = await task_planner.plan(instruction)
    # Returns: [Step(action="create_folder", params={...}), Step(...), ...]

    # 2. Validate (Permission Guard — Phase 6, stub for now)
    for step in plan.steps:
        validation = permission_guard.check(step)
        if not validation.allowed:
            return TaskResult(status="blocked", reason=validation.reason)
        if validation.needs_approval:
            await request_approval(step)

    # 3. Execute
    results = []
    for step in plan.steps:
        journal.log_before(step)
        try:
            result = await execution_engine.execute(step)
            journal.log_after(step, result)
            results.append(result)
        except Exception as e:
            journal.log_failure(step, e)
            await rollback_completed(results)
            return TaskResult(status="failed", error=str(e))

    # 4. Report
    return TaskResult(status="completed", results=results)
```

### 6.4 Completion Criteria

```
□ Agent Daemon starts and serves HTTP API on port 8900
□ POST /api/v1/task with "Create folder Test in Documents" → folder created
□ All operations logged in SQLite transaction journal
□ GET /api/v1/task/{id} returns correct status
□ Failed operations produce clear error messages
□ Rollback endpoint successfully undoes last operation
□ Health endpoint confirms Ollama connectivity
```

---


## 7. Phase 3: Windows Desktop Control

**Duration:** 6 days
**Goal:** Agent can control Windows GUI applications via multiple methods
**Milestone:** M3 — Agent opens Notepad, types text, and saves a file

### 7.1 Tasks

| # | Task | Time | Priority |
|---|------|:----:|:--------:|
| 3.1 | Install Microsoft UFO3 + configure for Ollama | 2 hours | Critical |
| 3.2 | Test UFO3: simple single-app task via CLI | 2 hours | Critical |
| 3.3 | Install agent-desktop binary + test snapshot | 1 hour | High |
| 3.4 | Build `GUIController` class (wraps multiple backends) | 4 hours | Critical |
| 3.5 | Implement agent-desktop backend in GUIController | 3 hours | High |
| 3.6 | Implement pywinauto backend in GUIController | 3 hours | High |
| 3.7 | Build `ApplicationRegistry` (known apps + their controls) | 3 hours | Medium |
| 3.8 | Build `GUIPlanner` prompt (convert instructions → GUI actions) | 3 hours | Critical |
| 3.9 | Integration: Agent Daemon → GUIController → real app | 4 hours | Critical |
| 3.10 | AutoHotkey scripts for common fast actions | 2 hours | Medium |
| 3.11 | Test suite: 10 common GUI tasks execute correctly | 4 hours | High |

### 7.2 GUI Controller Architecture

```python
# src/execution/gui_controller.py — Unified GUI control interface

class GUIController:
    """Unified interface for controlling Windows desktop applications.
    Routes to the best backend for each task type."""

    def __init__(self):
        self.backends = {
            "agent_desktop": AgentDesktopBackend(),   # Fast, accessibility-tree based
            "pywinauto": PywinautoBackend(),          # Battle-tested, reliable
            "ufo3": UFO3Backend(),                    # Most capable, AI-native
            "ahk": AutoHotkeyBackend(),              # Fastest execution, macros
        }

    async def execute_gui_action(self, action: GUIAction) -> GUIResult:
        """Choose best backend and execute."""
        backend = self._select_backend(action)
        return await backend.execute(action)

    def _select_backend(self, action: GUIAction) -> Backend:
        """Route to optimal backend based on action type."""
        if action.type == "hotkey" or action.type == "macro":
            return self.backends["ahk"]       # Fastest for keystrokes
        elif action.type == "click_element":
            return self.backends["agent_desktop"]  # Best for known elements
        elif action.type == "complex_workflow":
            return self.backends["ufo3"]      # Best for multi-step reasoning
        else:
            return self.backends["pywinauto"] # Safe fallback
```

### 7.3 Supported GUI Operations

| Operation | Primary Backend | Fallback |
|-----------|----------------|----------|
| Click button by name | agent-desktop | pywinauto |
| Type text in field | agent-desktop | pywinauto |
| Keyboard shortcut | AutoHotkey | pywinauto |
| Open application | pywinauto | shell exec |
| Multi-step app workflow | UFO3 | agent-desktop chain |
| Menu navigation | agent-desktop | pywinauto |
| File dialog interaction | pywinauto | agent-desktop |
| Scroll | agent-desktop | PyAutoGUI |
| Screenshot capture | PyAutoGUI | agent-desktop |
| Wait for element | agent-desktop | pywinauto |

### 7.4 Completion Criteria

```
□ UFO3 successfully controls at least 3 different Windows apps with Ollama
□ agent-desktop snapshot captures accessibility tree of File Explorer
□ agent-desktop click/type actions work on real UI elements
□ GUIController selects appropriate backend based on action type
□ Full test: "Open Notepad → type 'Hello World' → save as test.txt" succeeds
□ Full test: "Open File Explorer → create new folder → rename it" succeeds
□ Error handling: graceful failure if app is not open or element not found
□ ApplicationRegistry has entries for: File Explorer, Notepad, Browser, Settings
```

---

## 8. Phase 4: Orchestration & Remote Control

**Duration:** 6 days
**Goal:** Trigger agent from anywhere via Telegram/web, orchestrated through Hetzner n8n
**Milestone:** M4 — Telegram message triggers file operation on Windows PC

### 8.1 Tasks

| # | Task | Time | Priority |
|---|------|:----:|:--------:|
| 4.1 | Install Tailscale on Windows PC + authenticate | 10 min | Critical |
| 4.2 | Install Tailscale on Hetzner server | 10 min | Critical |
| 4.3 | Verify PC ↔ Hetzner direct communication via Tailscale | 20 min | Critical |
| 4.4 | Configure Agent Daemon to accept only Tailscale IPs | 1 hour | Critical |
| 4.5 | Create n8n workflow: Telegram → task → PC | 3 hours | Critical |
| 4.6 | Create n8n workflow: Cron schedule → task → PC | 2 hours | High |
| 4.7 | Create n8n workflow: webhook API → task → PC | 2 hours | High |
| 4.8 | Build Telegram command parser in n8n | 2 hours | Critical |
| 4.9 | Build result notification formatter (Telegram markdown) | 2 hours | High |
| 4.10 | Build approval workflow: agent asks → user approves in Telegram | 4 hours | Critical |
| 4.11 | Build task queue (handle PC-offline scenario) | 3 hours | High |
| 4.12 | Add new route in Cloudflare Tunnel config (agent API) | 15 min | Medium |
| 4.13 | End-to-end test: Telegram → Hetzner → PC → result → Telegram | 2 hours | Critical |
| 4.14 | Update Hetzner watchdog to monitor Tailscale + agent health | 1 hour | High |

### 8.2 Telegram Command Interface

```
TELEGRAM COMMANDS (messages to your bot):

/agent <instruction>     — Execute any agent task
  Example: /agent organize my downloads
  Example: /agent create a project folder structure for "MyApp"
  Example: /agent open Excel and create a monthly budget

/status                  — Check agent system health
/history [n]             — Show last N completed tasks
/rollback [task_id]      — Undo a specific task
/approve                 — Approve pending destructive action
/reject                  — Reject pending destructive action
/queue                   — Show queued tasks (if PC is offline)
/help                    — Show available commands
```

### 8.3 n8n Workflow Designs

**Workflow 1: "Agent Command Handler"**
```
[Telegram Trigger (webhook)]
  → [Code Node: parse command + validate admin]
  → [Switch: command type]
    → /agent: [HTTP Request → PC Agent Daemon via Tailscale]
                → [IF: needs approval?]
                  → YES: [Telegram: "Approve? /approve or /reject"]
                  → NO: [Wait for result → Telegram: report]
    → /status: [HTTP → PC /api/v1/health] → [Telegram: format + send]
    → /history: [HTTP → PC /api/v1/tasks?last=5] → [Telegram: list]
    → /rollback: [HTTP → PC /api/v1/rollback] → [Telegram: confirm]
```

**Workflow 2: "Scheduled Automation"**
```
[Cron Trigger: daily 2:00 AM Asia/Dubai]
  → [HTTP Request → PC: {"instruction": "organize downloads"}]
  → [Wait for response (timeout 5min)]
  → [IF: success]
    → YES: [Telegram: "✅ Daily organization: X files organized"]
    → NO: [Telegram: "❌ Daily org failed: {error}"]
```

**Workflow 3: "PC Health Monitor"**
```
[Cron Trigger: every 5 min]
  → [HTTP Request → PC /api/v1/health (timeout 10s)]
  → [IF: no response]
    → [Set variable: pc_offline = true]
    → [IF: wasn't offline before]
      → [Telegram: "⚠️ PC agent unreachable"]
  → [IF: response OK + was_offline]
    → [Telegram: "✅ PC agent back online"]
    → [Process queued tasks]
```

### 8.4 Completion Criteria

```
□ Tailscale installed on both PC and Hetzner, can ping each other
□ Agent Daemon only accepts connections from Tailscale subnet
□ /agent command in Telegram triggers real action on PC
□ Result notification arrives in Telegram within 30 seconds
□ Approval workflow: "delete" task pauses and asks for confirmation
□ Scheduled task fires at configured time automatically
□ PC-offline scenario: tasks queue, execute when PC reconnects
□ /status shows correct health info from PC
□ /rollback successfully undoes a previous task
```

---


## 9. Phase 5: File Intelligence System

**Duration:** 6 days
**Goal:** AI-powered file classification, automatic organization, content-aware naming
**Milestone:** M5 — Agent correctly classifies and organizes 10 diverse files

### 9.1 Tasks

| # | Task | Time | Priority |
|---|------|:----:|:--------:|
| 5.1 | Build content extraction pipeline (PDF, DOCX, images, code) | 4 hours | Critical |
| 5.2 | Build AI classification prompt (file → category/name/date) | 3 hours | Critical |
| 5.3 | Build folder structure template engine | 2 hours | High |
| 5.4 | Build duplicate detection (hash-based) | 2 hours | High |
| 5.5 | Build file renaming engine (convention enforcement) | 2 hours | High |
| 5.6 | Build watchdog service (monitor directories for changes) | 3 hours | Critical |
| 5.7 | Build batch organizer (process existing backlog of files) | 3 hours | High |
| 5.8 | Build staging mode (propose changes, don't execute until approved) | 3 hours | Critical |
| 5.9 | Build rollback system (undo organization by time range or task) | 3 hours | Critical |
| 5.10 | Build organization rules engine (user-defined folder templates) | 3 hours | High |
| 5.11 | Integration: watchdog → classify → organize → log → notify | 4 hours | Critical |
| 5.12 | Test with 50+ real files of mixed types | 3 hours | Critical |

### 9.2 Classification Pipeline Architecture

```
FILE ENTERS PIPELINE
       │
       ▼
┌─────────────────────────────┐
│  CONTENT EXTRACTION         │
│  .pdf → pymupdf text        │
│  .docx → python-docx text   │
│  .xlsx → openpyxl headers   │
│  .py/.js → first 50 lines   │
│  .jpg/.png → EXIF + filename│
│  .mp3/.mp4 → metadata       │
│  other → filename + size    │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  FAST CLASSIFICATION        │
│  Model: qwen3:0.8b (fast)   │
│  Input: filename + metadata  │
│  Output: {category, confidence}│
│  If confidence > 0.9 → skip │
│  full analysis               │
└────────────┬────────────────┘
             │ (low confidence)
             ▼
┌─────────────────────────────┐
│  DEEP CLASSIFICATION        │
│  Model: qwen3:8b (full)     │
│  Input: content preview +    │
│         metadata + context   │
│  Output: {                   │
│    category,                 │
│    subcategory,              │
│    suggested_name,           │
│    date,                     │
│    tags,                     │
│    confidence                │
│  }                          │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  RULES ENGINE               │
│  - Apply naming convention   │
│  - Check duplicate (hash)    │
│  - Validate destination     │
│  - Enforce max depth        │
│  - Generate destination path │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  STAGING (if mode=staging)   │
│  - Propose changes to user   │
│  - Wait for approval         │
│  OR                          │
│  EXECUTE (if mode=auto)      │
│  - Log to journal            │
│  - Move/rename file          │
│  - Verify success            │
│  - Notify                    │
└─────────────────────────────┘
```

### 9.3 Folder Structure Templates

```yaml
# config/folder_templates.yaml
templates:
  default:
    Documents:
      - Invoices/{year}-{month}/
      - Contracts/{year}/
      - Reports/{year}-{month}/
      - Personal/
      - Work/
    Code:
      - Python/
      - JavaScript/
      - Projects/
    Images:
      - Photos/{year}-{month}/
      - Screenshots/{year}-{month}/
      - Design/
    Videos:
      - Recordings/
      - Downloads/
    Audio:
      - Music/
      - Recordings/
    Archives:
      - Compressed/
      - Backups/
    Data:
      - Spreadsheets/
      - Databases/
      - Exports/
```

### 9.4 Completion Criteria

```
□ Content extraction works for: PDF, DOCX, XLSX, TXT, images, code files
□ Fast classification (0.8B) correctly categorizes 80%+ of simple files
□ Deep classification (8B) achieves 95%+ accuracy on test set
□ Watchdog detects new files in ~/Downloads within 3 seconds
□ Staging mode presents proposed changes without executing
□ Batch organizer processes 50+ files without errors
□ Rollback successfully moves all files back to original locations
□ Duplicate detection prevents organizing the same file twice
□ Full pipeline: new file appears → classified → organized → logged → notified (< 30 sec)
□ n8n scheduled workflow triggers nightly organization successfully
```

---

## 10. Phase 6: Security & Hardening

**Duration:** 5 days
**Goal:** Production-grade safety — no destructive action without approval, full auditability
**Milestone:** M6 — Attempt to delete a file is blocked, logged, and user is notified

### 10.1 Tasks

| # | Task | Time | Priority |
|---|------|:----:|:--------:|
| 6.1 | Implement full `PermissionGuard` class | 4 hours | Critical |
| 6.2 | Implement action classification (green/yellow/red/black) | 3 hours | Critical |
| 6.3 | Implement path validation (allowlist/blocklist) | 2 hours | Critical |
| 6.4 | Implement approval workflow (Telegram confirm/reject) | 3 hours | Critical |
| 6.5 | Implement rate limiting (max actions per minute) | 2 hours | High |
| 6.6 | Implement immutable audit log (append-only SQLite) | 3 hours | Critical |
| 6.7 | Implement transaction snapshots (before/after state) | 3 hours | High |
| 6.8 | Configure Windows user account for agent (standard, not admin) | 1 hour | High |
| 6.9 | Configure NTFS permissions on allowed directories | 1 hour | High |
| 6.10 | Build security test suite (attempt all dangerous operations) | 4 hours | Critical |
| 6.11 | Implement emergency kill switch (Telegram /stop command) | 2 hours | Critical |
| 6.12 | Document security model and threat model | 2 hours | Medium |

### 10.2 Action Classification Matrix

```python
# src/security/action_classifier.py

ACTION_CLASSES = {
    # GREEN — Auto-execute, log only
    "green": [
        "read_file", "list_directory", "search_files",
        "get_file_info", "check_status", "classify_file",
    ],

    # YELLOW — Execute + log + include in daily report
    "yellow": [
        "create_folder", "move_file", "rename_file",
        "copy_file", "write_file", "create_file",
    ],

    # RED — Require explicit user approval before execution
    "red": [
        "delete_file", "delete_folder", "overwrite_file",
        "empty_recycle_bin", "install_software",
        "modify_system_setting", "run_admin_command",
    ],

    # BLACK — Always blocked, never executed, alert immediately
    "black": [
        "format_drive", "modify_registry", "modify_startup",
        "access_credentials", "modify_ssh_keys",
        "disable_firewall", "disable_antivirus",
        "recursive_delete", "write_to_system_directory",
    ],
}
```

### 10.3 Security Test Cases (Must All Pass)

```python
# tests/test_security.py — ALL must pass before production deployment

def test_blocked_system_path():
    """Agent cannot write to C:/Windows"""
    result = permission_guard.check("write_file", Path("C:/Windows/test.txt"))
    assert result.allowed == False

def test_blocked_recursive_delete():
    """Agent cannot rm -rf anything"""
    result = permission_guard.check("recursive_delete", Path("C:/Users"))
    assert result.allowed == False
    assert result.classification == "black"

def test_delete_requires_approval():
    """File deletion pauses for user approval"""
    result = permission_guard.check("delete_file", Path("~/Organized/test.txt"))
    assert result.allowed == True
    assert result.needs_approval == True

def test_create_folder_auto_approved():
    """Creating folders in allowed paths is automatic"""
    result = permission_guard.check("create_folder", Path("~/Organized/New"))
    assert result.allowed == True
    assert result.needs_approval == False

def test_rate_limit_enforced():
    """Cannot execute more than 50 actions per minute"""
    for i in range(50):
        permission_guard.record_action()
    result = permission_guard.check("move_file", Path("~/test.txt"))
    assert result.allowed == False
    assert "rate limit" in result.reason.lower()

def test_kill_switch():
    """Emergency stop halts all operations immediately"""
    agent_daemon.emergency_stop()
    assert agent_daemon.is_stopped == True
    assert agent_daemon.accepts_new_tasks == False
```

### 10.4 Completion Criteria

```
□ PermissionGuard blocks ALL black-listed operations (100% block rate)
□ Red operations pause and request Telegram approval
□ Approval timeout (5 min) results in automatic rejection
□ Rate limiting prevents more than 50 file ops per minute
□ Audit log records every action with timestamp + before/after state
□ Kill switch (/stop) immediately halts all operations
□ Windows agent process runs as standard user (not admin)
□ NTFS permissions prevent writes outside allowed directories
□ Security test suite: all tests pass
□ Threat model document written and committed to repo
```

---


## 11. Phase 7: Production Deployment

**Duration:** 5 days
**Goal:** System runs unattended for 72+ hours without intervention
**Milestone:** M7 — 72-hour stability test passes with zero manual intervention

### 11.1 Tasks

| # | Task | Time | Priority |
|---|------|:----:|:--------:|
| 7.1 | Create Windows service wrapper (agent starts on boot) | 3 hours | Critical |
| 7.2 | Configure auto-start for Ollama + Agent Daemon | 1 hour | Critical |
| 7.3 | Build system health dashboard (n8n + Telegram daily report) | 3 hours | High |
| 7.4 | Implement graceful shutdown and restart procedures | 2 hours | High |
| 7.5 | Build comprehensive error recovery (auto-restart on crash) | 3 hours | Critical |
| 7.6 | Load testing: 100 tasks in sequence, verify no memory leaks | 4 hours | Critical |
| 7.7 | Integration testing: all Phase 1-6 capabilities together | 4 hours | Critical |
| 7.8 | Document all operational procedures (runbook) | 4 hours | High |
| 7.9 | Run 72-hour stability test | 72 hours | Critical |
| 7.10 | Fix any issues discovered during stability test | Variable | Critical |
| 7.11 | Create system backup procedure (agent configs + data) | 2 hours | High |
| 7.12 | Final documentation review and commit | 2 hours | Medium |

### 11.2 Windows Service Configuration

```python
# scripts/install_service.py — Register agent as Windows service

"""
Uses NSSM (Non-Sucking Service Manager) to create a Windows service
that auto-starts the Agent Daemon on boot.

Download NSSM: https://nssm.cc/download
"""

import subprocess

NSSM = r"C:\Tools\nssm.exe"
SERVICE_NAME = "MACAlAgent"
PYTHON = r"C:\Projects\macal-agent\.venv\Scripts\python.exe"
SCRIPT = r"C:\Projects\macal-agent\src\daemon\main.py"
LOG_DIR = r"C:\Projects\macal-agent\logs"

commands = [
    f'{NSSM} install {SERVICE_NAME} {PYTHON} {SCRIPT}',
    f'{NSSM} set {SERVICE_NAME} AppDirectory C:\\Projects\\macal-agent',
    f'{NSSM} set {SERVICE_NAME} AppStdout {LOG_DIR}\\service_stdout.log',
    f'{NSSM} set {SERVICE_NAME} AppStderr {LOG_DIR}\\service_stderr.log',
    f'{NSSM} set {SERVICE_NAME} AppRotateFiles 1',
    f'{NSSM} set {SERVICE_NAME} AppRotateBytes 10485760',  # 10MB
    f'{NSSM} set {SERVICE_NAME} Start SERVICE_AUTO_START',
    f'{NSSM} set {SERVICE_NAME} AppRestartDelay 5000',      # 5 sec restart delay
    f'{NSSM} start {SERVICE_NAME}',
]
```

### 11.3 Daily Health Report (Telegram)

```
📊 MACAL Agent — Daily Report (June 23, 2026)

System Status: 🟢 All Healthy
Uptime: 24h 0m (100%)
Ollama: Running (qwen3:8b loaded)
Agent Daemon: Running (port 8900)
Tailscale: Connected to Hetzner

Tasks Today:
  ✅ Completed: 12
  ❌ Failed: 0
  ⏸️ Awaiting Approval: 1
  🔄 Scheduled (tomorrow): 3

File Operations:
  📁 Files organized: 47
  📝 Files renamed: 12
  🗂️ Folders created: 3
  ↩️ Rollbacks: 0

Resource Usage:
  CPU: 3% avg / 45% peak
  RAM: 8.2 GB / 16 GB (51%)
  Disk: 142 GB free

⚠️ Alerts: None
```

### 11.4 Stability Test Protocol

```
72-HOUR STABILITY TEST PROCEDURE:

Setup:
1. Start all services (Ollama, Agent Daemon, Tailscale)
2. Verify all n8n workflows active on Hetzner
3. Enable monitoring (every 5 min health check)
4. Schedule: daily file organization at 2 AM
5. Schedule: hourly health report to Telegram
6. Queue 10 manual test tasks via Telegram

Pass Criteria (ALL must be met):
□ No service crashes in 72 hours
□ All scheduled tasks execute on time
□ All manual tasks complete successfully
□ Memory usage stays below 80% throughout
□ No file corruption or data loss
□ Agent recovers from intentional Ollama restart
□ Agent recovers from intentional network disconnection (30 sec)
□ All Telegram notifications delivered correctly
□ Audit log contains complete history of all operations
□ No error log entries of severity "CRITICAL"
```

---

## 12. Phase 8: Advanced Capabilities

**Duration:** Ongoing (post-production)
**Goal:** Expand agent capabilities incrementally based on real usage needs

### 12.1 Capability Expansion Roadmap

| Priority | Capability | Dependencies | Est. Effort |
|:--------:|-----------|-------------|:-----------:|
| 1 | **Multi-app workflows** (copy from app A → paste in app B) | Phase 3 complete | 1 week |
| 2 | **Browser automation** (Playwright MCP for web tasks) | Phase 2 complete | 3 days |
| 3 | **Email management** (read, classify, respond, archive) | Playwright MCP | 1 week |
| 4 | **Voice commands** (Whisper.cpp STT → agent) | Phase 4 complete | 3 days |
| 5 | **Learning from corrections** (remember user preferences) | Phase 5 complete | 1 week |
| 6 | **Screenshot analysis** (Qwen3-VL for visual tasks) | Phase 3 complete | 3 days |
| 7 | **Project scaffolding** (create full project structures) | Phase 2 complete | 2 days |
| 8 | **Calendar integration** (schedule-aware automation) | Phase 4 complete | 3 days |
| 9 | **Multi-PC coordination** (home PC + laptop) | Phase 4 complete | 1 week |
| 10 | **Natural language hotkeys** ("whenever I say X, do Y") | Phase 3 + AHK | 3 days |

### 12.2 Multi-App Workflow Example

```
USER: "Download the latest invoice from Gmail, rename it with today's
       date, save to Documents/Invoices/2026-06/, and add a row to
       my invoice tracker in Excel with the date and amount."

AGENT PLAN:
  Step 1: [Playwright MCP] Open Gmail → search "invoice" → download latest
  Step 2: [File Ops] Read PDF → extract date and amount via LLM
  Step 3: [File Ops] Rename: "invoice_2026-06-22_CompanyName_$150.pdf"
  Step 4: [File Ops] Move to ~/Documents/Invoices/2026-06/
  Step 5: [UFO3] Open Excel → invoice_tracker.xlsx
  Step 6: [UFO3] Add row: [2026-06-22, CompanyName, $150, "paid"]
  Step 7: [UFO3] Save and close
  Step 8: [Notify] "✅ Invoice processed: $150 from CompanyName"
```

---


## 13. Professional-Grade Requirements

### 13.1 Code Quality Standards

| Standard | Requirement |
|----------|------------|
| **Type safety** | Python type hints on ALL functions; mypy strict mode |
| **Error handling** | No bare `except:`; all errors typed, logged, and recoverable |
| **Logging** | Structured logging (JSON) with correlation IDs per task |
| **Configuration** | All settings in YAML config; zero hardcoded values |
| **Documentation** | Docstrings on all public functions; architecture decision records |
| **Testing** | Critical paths tested; security suite 100% coverage |
| **Naming** | Consistent naming: `snake_case` for Python, clear intent in names |
| **Dependencies** | Pinned in `requirements.txt`; minimal dependency count |
| **Secrets** | Never in code; environment variables or encrypted config |
| **Git** | Conventional commits; meaningful messages; no large binaries |

### 13.2 Reliability Requirements

| Requirement | Target | How Achieved |
|-------------|:------:|-------------|
| Agent uptime | 99%+ (when PC is on) | Windows service + auto-restart |
| Task success rate | 95%+ | Retry logic + fallback backends |
| Data loss prevention | Zero tolerance | Transaction journal + rollback |
| Recovery time | < 60 seconds | Auto-restart + health checks |
| Memory stability | No leaks over 72h | Resource limits + monitoring |
| Graceful degradation | Always | Each component independent |

### 13.3 Observability Requirements

| What | How | Where |
|------|-----|-------|
| Every task lifecycle | Structured log entries | `logs/agent.log` |
| Every file operation | Transaction journal | `data/audit.db` (SQLite) |
| Every LLM call | Token count + latency | `logs/llm.log` |
| System health | Periodic metrics | n8n health workflow |
| Errors | Immediate alert | Telegram notification |
| Daily summary | Aggregated report | Telegram daily digest |
| Performance trends | Weekly comparison | n8n report workflow |

### 13.4 Scalability Considerations

| Dimension | Current Design | 10x Scale Path |
|-----------|---------------|----------------|
| Tasks/day | 50-100 | Queue + parallel execution |
| Files/batch | 100 | Chunked processing + progress |
| Models loaded | 1-2 | Model routing (fast/full) |
| Connected devices | 1 PC | Multi-device via Tailscale mesh |
| Workflows | 5-10 n8n | Unlimited (n8n has no cap) |
| Storage | Local SSD | NAS mount or cloud sync |
| LLM capability | 8B model | Swap to 14B/32B as hardware allows |

### 13.5 Operational Runbook Requirements

Each component must have documented procedures for:
- Starting / stopping / restarting
- Checking health status
- Viewing logs
- Common failure modes and fixes
- Upgrade procedure
- Backup and restore
- Emergency shutdown

---

## 14. Risk Register & Mitigation

| # | Risk | Probability | Impact | Mitigation |
|---|------|:-----------:|:------:|-----------|
| 1 | Ollama model gives incorrect file operation | Medium | High | Permission Guard validates all paths; staging mode for bulk ops |
| 2 | Agent moves wrong files | Medium | High | Transaction journal enables instant rollback; daily backups |
| 3 | Memory leak crashes PC | Low | High | Resource limits; watchdog auto-restarts; 72h stability test |
| 4 | Tailscale free tier changes | Very Low | Medium | WireGuard self-hosted as fallback (already documented) |
| 5 | UFO3 project abandoned | Low | Medium | agent-desktop + pywinauto as complete fallback stack |
| 6 | Ollama breaking update | Low | Medium | Pin version in config; test before upgrading |
| 7 | n8n licensing change | Very Low | High | Self-hosted version grandfathered; Temporal as alt orchestrator |
| 8 | PC offline when task arrives | High | Low | Task queue on Hetzner; processes when PC reconnects |
| 9 | Hetzner server down | Very Low | Medium | Agent works standalone (no orchestration); auto-reconnects |
| 10 | SSH key lost | Very Low | Critical | Hetzner console access; key backup procedure documented |
| 11 | Accidental file deletion | Medium | High | NTFS permissions + action classification + staging mode |
| 12 | Model hallucination (wrong action) | Medium | Medium | Structured output parsing; validate before execute; approval gate |

### Contingency Plans

**If Ollama stops working:**
→ Open Interpreter still works standalone with any provider
→ Switch to llama.cpp directly (same models, different runtime)

**If UFO3 stops working:**
→ agent-desktop + pywinauto cover all GUI needs
→ AutoHotkey for critical macros

**If Hetzner server goes down:**
→ Agent continues working locally (CLI/hotkey triggers)
→ No remote access until server recovers
→ All data stays on PC (nothing lost)

**If Tailscale changes free tier:**
→ Switch to WireGuard peer-to-peer (config takes 10 min)
→ Or use Cloudflare Tunnel for PC agent API directly

---


## 15. Success Metrics

### 15.1 Phase Exit Criteria (Hard Gates)

Each phase MUST meet its exit criteria before the next phase begins:

| Phase | Gate Criteria | Verified By |
|:-----:|-------------|-------------|
| 0 | Pre-flight script passes 100% | Automated script |
| 1 | LLM produces valid tool calls consistently (10/10 tests) | Integration test |
| 2 | Agent creates folder from natural language (5/5 attempts) | Manual + automated |
| 3 | GUI automation works on 3+ apps (Notepad, Explorer, Browser) | Manual test |
| 4 | Telegram → action → result round-trip < 60 seconds | End-to-end test |
| 5 | 50-file batch organized with 95%+ accuracy | Batch test |
| 6 | ALL security tests pass (zero failures allowed) | Test suite |
| 7 | 72-hour unattended stability test passes | Monitoring data |

### 15.2 Long-Term Success Metrics (Ongoing)

| Metric | Target | Measurement |
|--------|:------:|-------------|
| Tasks completed per week | Growing (baseline → 2x) | n8n task counter |
| Task success rate | > 95% | Completed / Total |
| Average task duration | < 30 seconds (simple) | Agent logs |
| Time saved per week | > 2 hours | Manual estimate |
| Unplanned interventions | < 1 per week | Alert count |
| Rollbacks needed | < 5% of tasks | Journal query |
| Security violations | 0 (zero tolerance) | Security log |

### 15.3 System Health Indicators

```
🟢 HEALTHY:
  - All services running
  - Task success rate > 95%
  - No critical errors in 24h
  - Memory < 70%
  - Tailscale connected

🟡 DEGRADED:
  - One service restarted recently
  - Task success rate 80-95%
  - Non-critical errors present
  - Memory 70-85%

🔴 CRITICAL:
  - Service down and not recovering
  - Task success rate < 80%
  - Critical errors present
  - Memory > 85%
  - Tailscale disconnected > 5 min
```

---

## 16. Maintenance & Evolution

### 16.1 Regular Maintenance Schedule

| Task | Frequency | How |
|------|:---------:|-----|
| Review agent logs for errors | Weekly | `grep ERROR logs/agent.log` |
| Check disk usage (models + logs) | Weekly | n8n health report |
| Update Ollama models | Monthly | `ollama pull qwen3:8b` |
| Update Python dependencies | Monthly | `pip install --upgrade -r requirements.txt` |
| Review and prune audit log | Monthly | Keep 90 days, archive older |
| Test rollback procedure | Monthly | Execute test rollback |
| Update n8n (Hetzner) | Quarterly | `docker compose pull && up -d` |
| Review security posture | Quarterly | Run security test suite |
| Backup agent config + data | Daily (automated) | Script in Phase 7 |

### 16.2 Upgrade Paths

**When your hardware improves:**
- More RAM → run larger model (Qwen3-14B, Qwen3-32B)
- New GPU → significantly faster inference
- Second SSD → separate model storage from data

**When better models release:**
- Ollama `pull` → test → swap in config
- No code changes needed (model is a config parameter)
- A/B test: run new model on subset of tasks, compare quality

**When tools evolve:**
- UFO3 updates → `git pull` in UFO directory, test
- agent-desktop updates → download new binary, test
- Open Interpreter updates → `pip install --upgrade`, test

### 16.3 Decision Log Template

```markdown
# Decision: [Title]
## Date: YYYY-MM-DD
## Context: Why this decision was needed
## Options Considered:
1. Option A — pros/cons
2. Option B — pros/cons
## Decision: Which option and why
## Consequences: What this means for the system
## Review Date: When to revisit this decision
```

---

## Summary: The Complete Execution Checklist

```
═══════════════════════════════════════════════════════════════
  MACAL AGENT SYSTEM — MASTER EXECUTION CHECKLIST
═══════════════════════════════════════════════════════════════

PHASE 0: PREPARATION (Days 1-2)
  □ Hardware audit completed
  □ All software prerequisites installed
  □ Repository created with correct structure
  □ config/agent.yaml template in place
  □ Pre-flight verification passes 100%
  □ Git: first commit pushed

PHASE 1: FOUNDATION (Days 3-5)
  □ Ollama running with qwen3:8b loaded
  □ Python venv created with all dependencies
  □ OllamaClient class built and tested
  □ ToolRegistry class built and tested
  □ System prompts defined
  □ MILESTONE: LLM produces valid tool calls (10/10)

PHASE 2: INTELLIGENCE (Days 6-10)
  □ Agent Daemon serves HTTP API on port 8900
  □ TaskPlanner decomposes instructions into steps
  □ ExecutionEngine runs steps sequentially
  □ FileOperations executor handles create/move/rename
  □ TransactionJournal logs all operations
  □ Rollback endpoint works correctly
  □ MILESTONE: "Create folder X" works from API call

PHASE 3: DESKTOP CONTROL (Days 11-16)
  □ UFO3 installed and configured for Ollama
  □ agent-desktop CLI installed and taking snapshots
  □ GUIController class routes to correct backend
  □ pywinauto handles File Explorer operations
  □ AutoHotkey scripts for common fast actions
  □ MILESTONE: "Open Notepad, type Hello, save" works

PHASE 4: ORCHESTRATION (Days 17-22)
  □ Tailscale connecting PC ↔ Hetzner
  □ Agent Daemon accepts only Tailscale IPs
  □ n8n workflow: Telegram → agent task → result → notification
  □ n8n workflow: Cron schedule → agent task
  □ Approval workflow: Telegram confirm/reject
  □ Task queue handles PC-offline scenario
  □ MILESTONE: Telegram message triggers real PC action

PHASE 5: FILE INTELLIGENCE (Days 23-28)
  □ Content extraction pipeline (PDF, DOCX, images, code)
  □ Fast classification (0.8B) for obvious files
  □ Deep classification (8B) for ambiguous files
  □ Watchdog monitors directories for new files
  □ Staging mode proposes changes without executing
  □ Rollback system undoes organization by task
  □ MILESTONE: 50 files organized with 95%+ accuracy

PHASE 6: SECURITY (Days 29-33)
  □ PermissionGuard blocks all black-listed operations
  □ Red operations require Telegram approval
  □ Rate limiting enforced (50 ops/minute max)
  □ Immutable audit log records everything
  □ Agent runs as standard Windows user
  □ NTFS permissions restrict write paths
  □ Kill switch (/stop) works immediately
  □ ALL security tests pass (zero failures)
  □ MILESTONE: Destructive action blocked + logged + reported

PHASE 7: PRODUCTION (Days 34-38)
  □ Agent registered as Windows service (auto-start)
  □ Health dashboard reports via Telegram daily
  □ Error recovery: auto-restart on crash
  □ Load test: 100 tasks in sequence, no memory leak
  □ All Phase 1-6 capabilities working together
  □ Operational runbook documented
  □ MILESTONE: 72-hour stability test passes

PHASE 8: ADVANCED (Days 39+)
  □ Multi-app workflows crossing application boundaries
  □ Browser automation via Playwright MCP
  □ Voice commands (optional)
  □ Learning from corrections (optional)
  □ Continuous expansion based on real usage needs

═══════════════════════════════════════════════════════════════
  TOTAL ESTIMATED TIME: 38 days to production
  TOTAL NEW MONTHLY COST: $0.00
  INFRASTRUCTURE: Existing Hetzner + existing Windows PC
═══════════════════════════════════════════════════════════════
```

---

*Implementation Roadmap v1.0 — June 22, 2026*
*Designed for long-term scalability, zero vendor lock-in, and professional-grade reliability.*
*All tools MIT/Apache/BSD/GPL licensed. All infrastructure already owned.*
