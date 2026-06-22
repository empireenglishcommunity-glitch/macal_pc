"""
Ollama Client — Wrapper for the local Ollama LLM API.

Handles:
- Chat completions (single and multi-turn)
- Structured JSON output (forced schema)
- Tool/function calling (Ollama native format)
- Model switching (primary, fast, vision)
- Timeout handling and retry logic
- Streaming responses (optional)

Uses Ollama's native /api/chat endpoint which supports:
- System/user/assistant message roles
- Native tool/function calling (since Ollama 0.4+)
- JSON mode via format parameter
- Streaming and non-streaming responses

Usage:
    client = OllamaClient()
    response = await client.chat("Organize my downloads folder")
    response = await client.chat_with_tools(message, tools)
"""

from __future__ import annotations

import json
import logging
import time
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
    raw_response: dict[str, Any] = field(default_factory=dict)


class OllamaError(Exception):
    """Raised when Ollama API returns an error."""

    def __init__(self, message: str, status_code: int = 0) -> None:
        self.status_code = status_code
        super().__init__(message)


class OllamaClient:
    """Async client for the Ollama REST API.

    Connects to a locally running Ollama instance and provides
    chat completions with optional tool/function calling support.
    """

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

    async def _request_with_retry(
        self, endpoint: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a POST request with retry logic.

        Retries on timeout and connection errors up to max_retries times.
        """
        client = await self._get_client()
        url = f"{self.host}{endpoint}"
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    f"Ollama request (attempt {attempt}/{self.max_retries}): "
                    f"{endpoint} model={payload.get('model', 'unknown')}"
                )
                start = time.time()
                resp = await client.post(url, json=payload)
                elapsed_ms = int((time.time() - start) * 1000)

                if resp.status_code != 200:
                    error_text = resp.text[:500]
                    logger.error(f"Ollama error {resp.status_code}: {error_text}")
                    raise OllamaError(
                        f"Ollama returned {resp.status_code}: {error_text}",
                        status_code=resp.status_code,
                    )

                data = resp.json()
                data["_elapsed_ms"] = elapsed_ms
                return data

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                logger.warning(
                    f"Ollama request failed (attempt {attempt}): {type(e).__name__}: {e}"
                )
                if attempt < self.max_retries:
                    await self._sleep_backoff(attempt)

        raise OllamaError(
            f"All {self.max_retries} attempts failed. Last error: {last_error}"
        )

    @staticmethod
    async def _sleep_backoff(attempt: int) -> None:
        """Exponential backoff between retries."""
        import asyncio
        delay = min(2 ** attempt, 10)  # 2s, 4s, 8s, max 10s
        await asyncio.sleep(delay)

    async def chat(
        self,
        message: str,
        system_prompt: str = "",
        history: list[dict[str, str]] | None = None,
        json_mode: bool = False,
        model: str | None = None,
    ) -> LLMResponse:
        """Send a chat message and get a response.

        Args:
            message: The user message to send.
            system_prompt: Optional system prompt to set agent behavior.
            history: Optional conversation history (list of role/content dicts).
            json_mode: If True, force JSON output format.
            model: Override the default model for this call.

        Returns:
            LLMResponse with content and metadata.
        """
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": message})

        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        if json_mode:
            payload["format"] = "json"

        data = await self._request_with_retry("/api/chat", payload)

        # Parse response
        msg = data.get("message", {})
        content = msg.get("content", "")

        # Calculate tokens from Ollama response metadata
        tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
        elapsed = data.get("_elapsed_ms", 0)

        logger.info(
            f"Chat response: {len(content)} chars, {tokens} tokens, {elapsed}ms"
        )

        return LLMResponse(
            content=content,
            model=data.get("model", model or self.model),
            tokens_used=tokens,
            duration_ms=elapsed,
            raw_response=data,
        )

    async def chat_with_tools(
        self,
        message: str,
        tools: list[dict[str, Any]],
        system_prompt: str = "",
        model: str | None = None,
    ) -> LLMResponse:
        """Send a message with tool definitions, get tool calls back.

        Uses Ollama's native tool calling support. The LLM returns
        structured tool_calls in the response message when it determines
        a tool should be invoked.

        Args:
            message: The user instruction.
            tools: List of tool definitions (OpenAI function-calling format).
            system_prompt: Optional system prompt.
            model: Override the default model for this call.

        Returns:
            LLMResponse with parsed tool_calls list.
        """
        messages: list[dict[str, Any]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": message})

        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
            "tools": tools,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        data = await self._request_with_retry("/api/chat", payload)

        # Parse response
        msg = data.get("message", {})
        content = msg.get("content", "")
        raw_tool_calls = msg.get("tool_calls", [])

        # Parse tool calls from Ollama native format
        tool_calls: list[ToolCall] = []
        for tc in raw_tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            arguments = func.get("arguments", {})
            if name:
                tool_calls.append(ToolCall(name=name, arguments=arguments))

        # If no native tool calls but content looks like JSON tool call,
        # try to parse it (fallback for models that output JSON instead)
        if not tool_calls and content.strip():
            parsed = self._try_parse_tool_calls_from_content(content)
            if parsed:
                tool_calls = parsed

        tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
        elapsed = data.get("_elapsed_ms", 0)

        logger.info(
            f"Tool call response: {len(tool_calls)} tool(s), "
            f"{tokens} tokens, {elapsed}ms"
        )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            model=data.get("model", model or self.model),
            tokens_used=tokens,
            duration_ms=elapsed,
            raw_response=data,
        )

    @staticmethod
    def _try_parse_tool_calls_from_content(content: str) -> list[ToolCall]:
        """Attempt to parse tool calls from plain-text JSON output.

        Some models return tool calls as JSON in the content field
        rather than in the dedicated tool_calls field. This handles
        both single-call and multi-call JSON formats.
        """
        # Strip thinking tags if present (Qwen3 thinking mode)
        text = content.strip()
        if "<think>" in text:
            # Remove everything between <think> and </think>
            import re
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        if not text:
            return []

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in text:
                start = text.index("```json") + 7
                end = text.index("```", start)
                try:
                    data = json.loads(text[start:end].strip())
                except (json.JSONDecodeError, ValueError):
                    return []
            elif "```" in text:
                start = text.index("```") + 3
                end = text.index("```", start)
                try:
                    data = json.loads(text[start:end].strip())
                except (json.JSONDecodeError, ValueError):
                    return []
            else:
                return []

        # Handle single tool call: {"name": "...", "arguments": {...}}
        if isinstance(data, dict):
            if "name" in data and "arguments" in data:
                return [ToolCall(name=data["name"], arguments=data["arguments"])]
            # Handle: {"tool": "...", "params": {...}}
            if "tool" in data and "params" in data:
                return [ToolCall(name=data["tool"], arguments=data["params"])]

        # Handle array of tool calls
        if isinstance(data, list):
            calls = []
            for item in data:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("tool") or ""
                    args = item.get("arguments") or item.get("params") or {}
                    if name:
                        calls.append(ToolCall(name=name, arguments=args))
            return calls

        return []

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
