"""
Agent Daemon — Main entry point for the MACAL Agent HTTP service.

This is the always-running service on the Windows PC that:
1. Listens for task requests (from n8n/Hetzner via Tailscale)
2. Plans task execution using the local LLM
3. Executes actions through the execution layer
4. Reports results back to the orchestrator

Start:
    python -m src.daemon.main
    # Or via uvicorn:
    uvicorn src.daemon.main:app --host 0.0.0.0 --port 8900
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown logic for the agent daemon."""
    logger.info("MACAL Agent Daemon starting...")
    # TODO Phase 2: Initialize OllamaClient, ToolRegistry, ExecutionEngine
    yield
    logger.info("MACAL Agent Daemon shutting down...")
    # TODO Phase 2: Close connections, flush logs


app = FastAPI(
    title="MACAL Agent Daemon",
    description="AI Desktop Agent — receives tasks, plans execution, reports results",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/api/v1/health")
async def health_check() -> dict:
    """System health endpoint — used by n8n monitor workflow."""
    # TODO Phase 2: Check Ollama connectivity, report real status
    return {
        "status": "healthy",
        "version": "0.1.0",
        "ollama": "not_checked",
    }


@app.post("/api/v1/task")
async def submit_task(instruction: str = "") -> dict:
    """Submit a new task for the agent to execute.

    Called by n8n workflows on Hetzner when a trigger fires.
    """
    # TODO Phase 2: Implement full task lifecycle
    # 1. Validate instruction
    # 2. Plan with LLM
    # 3. Check permissions
    # 4. Execute steps
    # 5. Return result
    return {
        "task_id": "not_implemented",
        "status": "phase_2_pending",
        "message": "Agent daemon scaffolding — task execution not yet implemented",
    }


@app.post("/api/v1/rollback")
async def rollback_task(task_id: str = "", last_n: int = 0) -> dict:
    """Rollback a previous task or the last N operations."""
    # TODO Phase 2: Implement rollback from transaction journal
    return {"status": "not_implemented", "message": "Rollback coming in Phase 2"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8900, log_level="info")
