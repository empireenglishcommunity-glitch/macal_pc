"""
Ollama Client — Wrapper for the local Ollama LLM API.

Handles:
- Chat completions (single and multi-turn)
- Structured JSON output (forced schema)
- Tool/function calling format
- Model switching (primary, fast, vision)
- Timeout handling and retry logic
- Streaming responses (optional)

Usage:
    client = OllamaClient()
    response = await client.chat("Organize my downloads folder")
    tool_calls = await client.chat_with_tools(message, tools)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """A single tool/function call parsed from LLM output."""

    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Structured response from the LLM."""

    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    model: str = ""
    tokens_used: int = 0
    duration_ms: int = 0


class OllamaClient:
    """Async client for the Ollama REST API (OpenAI-compatible)."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "qwen3:8b",
        timeout: int = 120,
        max_retries: int = 3,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-initialize the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def chat(
        self,
        message: str,
        system_prompt: str = "",
        history: list[dict[str, str]] | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Send a chat message and get a response.

        Args:
            message: The user message to send.
            system_prompt: Optional system prompt to set agent behavior.
            history: Optional conversation history (list of role/content dicts).
            json_mode: If True, force JSON output format.

        Returns:
            LLMResponse with content and metadata.
        """
        # TODO: Implement in Phase 1 (Task 1.4)
        raise NotImplementedError("Phase 1: Implement OllamaClient.chat()")

    async def chat_with_tools(
        self,
        message: str,
        tools: list[dict[str, Any]],
        system_prompt: str = "",
    ) -> LLMResponse:
        """Send a message with tool definitions, parse tool calls from response.

        Args:
            message: The user instruction.
            tools: List of tool definitions (JSON Schema format).
            system_prompt: Optional system prompt.

        Returns:
            LLMResponse with parsed tool_calls.
        """
        # TODO: Implement in Phase 1 (Task 1.6)
        raise NotImplementedError("Phase 1: Implement OllamaClient.chat_with_tools()")

    async def health_check(self) -> bool:
        """Check if Ollama is running and responding."""
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.host}/api/tags")
            return resp.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    async def list_models(self) -> list[str]:
        """List all available models on the local Ollama instance."""
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.host}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except (httpx.RequestError, httpx.TimeoutException):
            pass
        return []

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
