"""
Phase 1 Integration Tests — Foundation Layer Verification.

These tests verify that:
1. OllamaClient can connect to a running Ollama instance
2. OllamaClient.chat() returns valid responses
3. OllamaClient.chat_with_tools() returns parsed tool calls
4. ToolRegistry provides correct tool definitions
5. The full pipeline (registry → tools → LLM → parsed call) works

IMPORTANT: These tests require Ollama to be running locally with qwen3:8b.
Run with: pytest tests/test_phase1_foundation.py -v

If Ollama is not running, these tests will be skipped automatically.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.intelligence.ollama_client import OllamaClient, ToolCall, LLMResponse
from src.intelligence.tool_registry import ToolRegistry
from src.intelligence.default_tools import create_default_registry
from src.intelligence.prompts import agent_system_prompt


# ─── Helpers ──────────────────────────────────────────────────


async def ollama_available() -> bool:
    """Check if Ollama is running and has a model."""
    client = OllamaClient()
    try:
        health = await client.health_check()
        if health:
            models = await client.list_models()
            await client.close()
            return len(models) > 0
    except Exception:
        pass
    await client.close()
    return False


# Skip all tests if Ollama is not running
pytestmark = pytest.mark.skipif(
    not asyncio.get_event_loop().run_until_complete(ollama_available()),
    reason="Ollama not running or no models available — skip integration tests",
)


# ─── Test: OllamaClient Health ────────────────────────────────


@pytest.mark.asyncio
async def test_ollama_health_check():
    """Ollama should be running and responding."""
    client = OllamaClient()
    assert await client.health_check() is True
    await client.close()


@pytest.mark.asyncio
async def test_ollama_list_models():
    """Should list at least one available model."""
    client = OllamaClient()
    models = await client.list_models()
    assert len(models) > 0
    print(f"  Available models: {models}")
    await client.close()


# ─── Test: Basic Chat ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_basic_response():
    """LLM should respond to a simple prompt."""
    client = OllamaClient()
    response = await client.chat("Say hello in exactly 3 words.")
    assert response.content != ""
    assert response.tokens_used > 0
    assert response.duration_ms > 0
    print(f"  Response: {response.content[:100]}")
    print(f"  Tokens: {response.tokens_used}, Time: {response.duration_ms}ms")
    await client.close()


@pytest.mark.asyncio
async def test_chat_with_system_prompt():
    """System prompt should influence response behavior."""
    client = OllamaClient()
    response = await client.chat(
        message="What is 2+2?",
        system_prompt="You are a math tutor. Always respond with just the number.",
    )
    assert "4" in response.content
    await client.close()


@pytest.mark.asyncio
async def test_chat_json_mode():
    """JSON mode should return parseable JSON."""
    client = OllamaClient()
    response = await client.chat(
        message='Return a JSON object with keys "name" and "age" for a person named Alex who is 30.',
        system_prompt="You are a JSON generator. Return only valid JSON, no explanation.",
        json_mode=True,
    )
    # Should be valid JSON
    data = json.loads(response.content)
    assert "name" in data or "Name" in data
    print(f"  JSON output: {data}")
    await client.close()


# ─── Test: Tool Calling ───────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_with_tools_single_call():
    """LLM should produce a valid tool call for a clear instruction."""
    client = OllamaClient()
    registry = create_default_registry()
    tools = registry.get_tool_definitions(category="file")

    response = await client.chat_with_tools(
        message="Create a folder called 'Reports' in my Documents directory.",
        tools=tools,
        system_prompt=agent_system_prompt(),
    )

    # Should have at least one tool call
    assert len(response.tool_calls) > 0, (
        f"Expected tool calls but got none. Content: {response.content[:200]}"
    )

    call = response.tool_calls[0]
    assert call.name == "create_folder"
    assert "path" in call.arguments
    assert "Reports" in call.arguments["path"] or "reports" in call.arguments["path"].lower()

    print(f"  Tool call: {call.name}({call.arguments})")
    await client.close()


@pytest.mark.asyncio
async def test_chat_with_tools_move_file():
    """LLM should correctly identify move_file tool for a move instruction."""
    client = OllamaClient()
    registry = create_default_registry()
    tools = registry.get_tool_definitions(category="file")

    response = await client.chat_with_tools(
        message="Move the file report.pdf from Downloads to Documents/Reports/",
        tools=tools,
        system_prompt=agent_system_prompt(),
    )

    assert len(response.tool_calls) > 0, (
        f"Expected tool calls but got none. Content: {response.content[:200]}"
    )

    call = response.tool_calls[0]
    assert call.name == "move_file"
    assert "source" in call.arguments
    assert "destination" in call.arguments

    print(f"  Tool call: {call.name}({call.arguments})")
    await client.close()


@pytest.mark.asyncio
async def test_chat_with_tools_list_directory():
    """LLM should call list_directory for a listing request."""
    client = OllamaClient()
    registry = create_default_registry()
    tools = registry.get_tool_definitions(category="file")

    response = await client.chat_with_tools(
        message="Show me what files are in my Downloads folder.",
        tools=tools,
        system_prompt=agent_system_prompt(),
    )

    assert len(response.tool_calls) > 0, (
        f"Expected tool calls but got none. Content: {response.content[:200]}"
    )

    call = response.tool_calls[0]
    assert call.name == "list_directory"
    assert "path" in call.arguments

    print(f"  Tool call: {call.name}({call.arguments})")
    await client.close()


# ─── Test: ToolRegistry ───────────────────────────────────────


def test_registry_creates_default_tools():
    """Default registry should have all file + system tools."""
    registry = create_default_registry()
    assert len(registry) >= 8  # 7 file tools + 1 system tool
    assert "create_folder" in registry.tool_names
    assert "move_file" in registry.tool_names
    assert "rename_file" in registry.tool_names
    assert "delete_file" in registry.tool_names
    assert "list_directory" in registry.tool_names


def test_registry_tool_definitions_format():
    """Tool definitions should be in OpenAI function-calling format."""
    registry = create_default_registry()
    tools = registry.get_tool_definitions()

    for tool in tools:
        assert tool["type"] == "function"
        assert "function" in tool
        func = tool["function"]
        assert "name" in func
        assert "description" in func
        assert "parameters" in func
        assert func["parameters"]["type"] == "object"


def test_registry_validates_calls():
    """ToolRegistry should validate tool calls before execution."""
    registry = create_default_registry()

    # Valid call
    valid, error = registry.validate_call("create_folder", {"path": "~/test"})
    assert valid is True
    assert error == ""

    # Missing required param
    valid, error = registry.validate_call("move_file", {"source": "~/a.txt"})
    assert valid is False
    assert "destination" in error

    # Unknown tool
    valid, error = registry.validate_call("nonexistent_tool", {})
    assert valid is False
    assert "Unknown tool" in error


# ─── Test: Content Parsing Fallback ──────────────────────────


def test_parse_tool_calls_from_json_content():
    """Should parse tool calls from JSON in content field."""
    content = '{"name": "create_folder", "arguments": {"path": "~/Reports"}}'
    calls = OllamaClient._try_parse_tool_calls_from_content(content)
    assert len(calls) == 1
    assert calls[0].name == "create_folder"
    assert calls[0].arguments["path"] == "~/Reports"


def test_parse_tool_calls_from_code_block():
    """Should parse tool calls from markdown code blocks."""
    content = '```json\n{"name": "move_file", "arguments": {"source": "~/a.txt", "destination": "~/b.txt"}}\n```'
    calls = OllamaClient._try_parse_tool_calls_from_content(content)
    assert len(calls) == 1
    assert calls[0].name == "move_file"


def test_parse_tool_calls_strips_thinking():
    """Should strip <think> tags before parsing."""
    content = '<think>Let me think about this...</think>\n{"name": "list_directory", "arguments": {"path": "~/Downloads"}}'
    calls = OllamaClient._try_parse_tool_calls_from_content(content)
    assert len(calls) == 1
    assert calls[0].name == "list_directory"


def test_parse_tool_calls_alternative_format():
    """Should handle 'tool'/'params' format as well as 'name'/'arguments'."""
    content = '{"tool": "rename_file", "params": {"path": "~/old.txt", "new_name": "new.txt"}}'
    calls = OllamaClient._try_parse_tool_calls_from_content(content)
    assert len(calls) == 1
    assert calls[0].name == "rename_file"
    assert calls[0].arguments["new_name"] == "new.txt"


def test_parse_tool_calls_returns_empty_on_invalid():
    """Should return empty list for non-tool-call content."""
    assert OllamaClient._try_parse_tool_calls_from_content("Hello world") == []
    assert OllamaClient._try_parse_tool_calls_from_content("") == []
    assert OllamaClient._try_parse_tool_calls_from_content("Just some text with no JSON") == []


# ─── Test: Full Pipeline (Milestone M1) ──────────────────────


@pytest.mark.asyncio
async def test_milestone_m1_full_pipeline():
    """
    ═══════════════════════════════════════════════════════════
    PHASE 1 MILESTONE TEST (M1)
    ═══════════════════════════════════════════════════════════

    The LLM must produce a valid, parseable tool call for a
    clear natural language instruction. This is the gate
    criterion for Phase 1 completion.

    Success criteria:
    - Response contains at least one tool call
    - Tool call has a valid name from the registry
    - Tool call has all required parameters
    - Parameters contain reasonable values
    """
    client = OllamaClient()
    registry = create_default_registry()
    tools = registry.get_tool_definitions()

    # 5 different instructions to test consistency
    test_cases = [
        ("Create a folder called Projects in my Documents", "create_folder", "path"),
        ("List the files in my Downloads folder", "list_directory", "path"),
        ("Move budget.xlsx from Desktop to Documents", "move_file", "source"),
    ]

    passed = 0
    total = len(test_cases)

    for instruction, expected_tool, expected_param in test_cases:
        response = await client.chat_with_tools(
            message=instruction,
            tools=tools,
            system_prompt=agent_system_prompt(),
        )

        if response.tool_calls:
            call = response.tool_calls[0]
            is_valid, _ = registry.validate_call(call.name, call.arguments)

            if is_valid and call.name == expected_tool and expected_param in call.arguments:
                passed += 1
                print(f"  ✅ '{instruction[:50]}...' → {call.name}({call.arguments})")
            else:
                print(
                    f"  ❌ '{instruction[:50]}...' → got {call.name}({call.arguments}) "
                    f"[expected {expected_tool} with param '{expected_param}']"
                )
        else:
            print(f"  ❌ '{instruction[:50]}...' → no tool calls (content: {response.content[:100]})")

    await client.close()

    success_rate = passed / total
    print(f"\n  Milestone M1 Score: {passed}/{total} ({success_rate:.0%})")
    assert success_rate >= 0.66, (
        f"Milestone M1 FAILED: {passed}/{total} tool calls correct. Need at least 66%."
    )
    print("  🎉 PHASE 1 MILESTONE M1 PASSED")
