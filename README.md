# MACAL Agent System

**Professional-grade AI Desktop Agent for Windows 11**

Self-hosted, zero recurring cost, zero vendor lock-in. Powered entirely by local LLM inference.

---

## What This Is

An AI agent that controls, manages, and organizes your Windows 11 desktop through natural language — triggered from Telegram, scheduled via n8n, or invoked directly from the terminal.

```
You say: "Organize my Downloads folder"
Agent does: classifies 47 files → creates folder structure → moves everything → reports back
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│  HETZNER SERVER (orchestration, always-on)       │
│  n8n workflows + Cloudflare Tunnel + Tailscale   │
└────────────────────┬────────────────────────────┘
                     │ encrypted mesh
┌────────────────────┴────────────────────────────┐
│  WINDOWS 11 PC (execution + local LLM)           │
│  Ollama + Agent Daemon + UFO3 + agent-desktop    │
└──────────────────────────────────────────────────┘
```

## Key Capabilities

| Capability | Status | Phase |
|-----------|:------:|:-----:|
| Local LLM inference (Ollama + Qwen3-8B) | Scaffolded | 1 |
| File operations (create, move, rename, organize) | Scaffolded | 2 |
| Windows GUI automation (UFO3, agent-desktop, pywinauto) | Scaffolded | 3 |
| Remote trigger (Telegram, n8n webhooks, cron) | Planned | 4 |
| AI file classification and organization | Scaffolded | 5 |
| Security framework (permission guard, audit log) | Scaffolded | 6 |
| Production deployment (Windows service, monitoring) | Planned | 7 |

## Quick Start

### Prerequisites

- Windows 11 (24H2 recommended)
- Python 3.11+
- Ollama installed (`winget install Ollama`)
- Model pulled (`ollama pull qwen3:8b`)

### Setup

```bash
# Clone
git clone https://github.com/empireenglishcommunity-glitch/macal_pc.git
cd macal_pc

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify everything is ready
python scripts/verify_setup.py
```

### Run the Agent Daemon

```bash
python -m src.daemon.main
# API available at http://localhost:8900
# Health check: GET http://localhost:8900/api/v1/health
```

## Project Structure

```
macal_pc/
├── src/
│   ├── daemon/              # HTTP service (receives + routes tasks)
│   │   └── main.py          # FastAPI app (health, task, rollback endpoints)
│   ├── intelligence/        # LLM integration
│   │   ├── ollama_client.py # Async Ollama API wrapper
│   │   ├── tool_registry.py # Tool definitions for function calling
│   │   └── prompts.py       # All prompt templates
│   ├── execution/           # Action executors
│   │   ├── file_operations.py  # Safe file management with audit
│   │   └── gui_controller.py   # Unified Windows GUI automation
│   ├── security/            # Safety layer
│   │   └── permission_guard.py # Action classification + path validation
│   └── file_organizer/      # AI file classification
│       └── classifier.py    # Two-tier content analysis
├── config/
│   └── agent.yaml           # Master configuration (all settings)
├── scripts/
│   └── verify_setup.py      # Pre-flight prerequisite checker
├── tests/
│   └── test_permission_guard.py  # Security test suite
├── logs/                    # Runtime logs (gitignored)
├── data/                    # SQLite databases, state (gitignored)
├── docs/                    # Architecture docs
├── n8n_workflows/           # Exported workflow JSONs
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project metadata + tool config
└── IMPLEMENTATION_ROADMAP.md # Full 8-phase development plan
```

## Configuration

All settings live in `config/agent.yaml`:

- **Ollama**: model selection, timeouts, temperature
- **Agent Daemon**: port, allowed origins, queue size
- **Security**: path allowlists/blocklists, action classification, rate limits
- **File Organizer**: watch directories, folder templates, staging mode
- **GUI**: backend selection, action delays
- **Notifications**: Telegram alerts, daily reports
- **Logging**: structured JSON logs, audit database

## Security Model

Every action passes through the Permission Guard before execution:

| Classification | Actions | Behavior |
|:-:|-----------|----------|
| **GREEN** | read, list, search | Auto-execute |
| **YELLOW** | create, move, rename | Execute + log |
| **RED** | delete, overwrite | Require approval |
| **BLACK** | format, registry, startup | Always blocked |

Additional protections:
- Path allowlists (agent can only write to designated folders)
- Rate limiting (max 50 operations/minute)
- Transaction journal (every op logged, full rollback support)
- Kill switch (immediate halt via Telegram `/stop`)

## Monthly Cost

| Component | Cost |
|-----------|:----:|
| Ollama + Qwen3-8B (local) | $0 |
| n8n (already on Hetzner) | $0 |
| Tailscale (free tier) | $0 |
| Cloudflare Tunnel (free) | $0 |
| **Total new cost** | **$0** |

## Development Roadmap

See [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) for the full 8-phase, 38-day plan.

Current status: **Phase 0 complete** — project scaffolded, ready for Phase 1.

## Design Principles

- **Zero vendor lock-in** — MIT/Apache/BSD tools only
- **Zero new recurring cost** — uses existing hardware + server
- **Offline-capable** — all LLM inference runs locally
- **Observable** — every action logged and traceable
- **Safe by default** — destructive ops require explicit approval
- **Incremental** — each phase delivers independently usable capability

## License

MIT
