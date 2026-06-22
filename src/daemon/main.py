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
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from pydantic import BaseModel

from src.intelligence.ollama_client import OllamaClient
from src.intelligence.tool_registry import ToolRegistry
from src.intelligence.default_tools import create_default_registry
from src.intelligence.prompts import agent_system_prompt
from src.execution.engine import ExecutionEngine

logger = logging.getLogger(__name__)

# ─── Global State ─────────────────────────────────────────────

_ollama: OllamaClient | None = None
_registry: ToolRegistry | None = None
_engine: ExecutionEngine | None = None
_start_time: float = 0.0


# ─── Request/Response Models ──────────────────────────────────


class TaskRequest(BaseModel):
    """Request body for task submission."""

    instruction: str
    context: dict = {}
    priority: str = "normal"


# ─── Lifespan ─────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown logic for the agent daemon."""
    global _ollama, _registry, _engine, _start_time

    logger.info("MACAL Agent Daemon starting...")
    _start_time = time.time()

    # Initialize Ollama client (use OLLAMA_MODEL env var, or detect available model)
    import os
    model = os.environ.get("OLLAMA_MODEL", "qwen3:4b")
    _ollama = OllamaClient(model=model)
    health = await _ollama.health_check()
    if health:
        models = await _ollama.list_models()
        logger.info(f"Ollama connected. Available models: {models}")
    else:
        logger.warning("Ollama not reachable — agent will retry on task submission")

    # Initialize tool registry
    _registry = create_default_registry()
    logger.info(f"Tool registry loaded: {len(_registry)} tools registered")

    # Initialize execution engine
    _engine = ExecutionEngine()
    logger.info("Execution engine ready")

    yield

    logger.info("MACAL Agent Daemon shutting down...")
    if _ollama:
        await _ollama.close()


# ─── App ──────────────────────────────────────────────────────

app = FastAPI(
    title="MACAL Agent Daemon",
    description="AI Desktop Agent — receives tasks, plans execution, reports results",
    version="0.2.0",
    lifespan=lifespan,
)


# ─── Endpoints ────────────────────────────────────────────────


@app.get("/api/v1/health")
async def health_check() -> dict:
    """System health endpoint — used by n8n monitor workflow.

    Returns real-time status of all subsystems.
    """
    ollama_ok = await _ollama.health_check() if _ollama else False
    uptime = int(time.time() - _start_time) if _start_time else 0
    models = await _ollama.list_models() if _ollama and ollama_ok else []

    return {
        "status": "healthy" if ollama_ok else "degraded",
        "version": "0.2.0",
        "uptime_seconds": uptime,
        "ollama": {
            "connected": ollama_ok,
            "models": models,
        },
        "tools_registered": len(_registry) if _registry else 0,
    }


@app.get("/api/v1/tools")
async def list_tools() -> dict:
    """List all available tools the agent can use."""
    if not _registry:
        return {"tools": [], "count": 0}
    return {
        "tools": _registry.tool_names,
        "count": len(_registry),
        "definitions": _registry.get_tool_definitions(),
    }


@app.post("/api/v1/task")
async def submit_task(request: TaskRequest) -> dict:
    """Submit a task for the agent to plan AND execute.

    Flow:
    1. LLM plans which tools to call
    2. Permission Guard checks each action
    3. Execution Engine performs the actions
    4. Returns results
    """
    if not request.instruction.strip():
        return {"error": "Empty instruction", "status": "rejected"}

    if not _ollama or not _registry or not _engine:
        return {"error": "Agent not initialized", "status": "error"}

    try:
        # Step 1: Ask LLM to plan
        tools = _registry.get_tool_definitions()
        response = await _ollama.chat_with_tools(
            message=request.instruction,
            tools=tools,
            system_prompt=agent_system_prompt(),
        )

        planned_calls = [
            {"tool": tc.name, "arguments": tc.arguments}
            for tc in response.tool_calls
        ]

        if not planned_calls:
            return {
                "status": "no_action",
                "instruction": request.instruction,
                "llm_response": response.content[:500],
                "message": "LLM did not produce any tool calls for this instruction",
            }

        # Step 2: Execute the plan
        task_result = await _engine.execute_plan(
            instruction=request.instruction,
            planned_actions=planned_calls,
        )

        # Step 3: Return full result
        return {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "instruction": request.instruction,
            "steps_completed": task_result.steps_completed,
            "steps_total": task_result.steps_total,
            "results": [
                {
                    "step": r.step_number,
                    "tool": r.tool,
                    "arguments": r.arguments,
                    "success": r.success,
                    "result": r.result,
                    "error": r.error,
                }
                for r in task_result.results
            ],
            "error": task_result.error,
            "duration_ms": task_result.duration_ms,
            "planning_tokens": response.tokens_used,
        }

    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        return {"error": str(e), "status": "failed"}


@app.post("/api/v1/chat")
async def chat(message: str = "", system_prompt: str = "") -> dict:
    """Direct chat with the local LLM (for testing/debugging)."""
    if not _ollama:
        return {"error": "Ollama not connected"}

    try:
        response = await _ollama.chat(
            message=message,
            system_prompt=system_prompt or agent_system_prompt(),
        )
        return {
            "content": response.content,
            "tokens_used": response.tokens_used,
            "duration_ms": response.duration_ms,
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/v1/rollback")
async def rollback_task(task_id: str = "", last_n: int = 0) -> dict:
    """Rollback a previous task or the last N operations."""
    if not _engine:
        return {"error": "Engine not initialized", "status": "error"}
    log = _engine.get_transaction_log()
    return {"status": "ok", "transaction_count": len(log), "recent": log[-5:] if log else []}


# ─── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8900, log_level="info")
