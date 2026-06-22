"""
Tool Registry — Defines and manages tools available to the AI agent.

The registry holds tool definitions (name, description, parameters) in
JSON Schema format compatible with OpenAI function-calling conventions.
It handles registration, lookup, parameter validation, and serialization.

Usage:
    registry = ToolRegistry()
    registry.register(
        name="create_folder",
        description="Create a new folder at the specified path",
        parameters={"path": {"type": "string", "description": "Folder path to create"}}
    )
    tools = registry.get_tool_definitions()  # Pass to LLM
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """A single tool that the agent can invoke."""

    name: str
    description: str
    parameters: dict[str, Any]
    required_params: list[str] = field(default_factory=list)
    category: str = "general"  # For grouping: "file", "gui", "shell", "system"


class ToolRegistry:
    """Registry of all tools available to the AI agent.

    Tools are registered at startup and their definitions are passed
    to the LLM so it knows what actions it can take.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        required: list[str] | None = None,
        category: str = "general",
    ) -> None:
        """Register a new tool.

        Args:
            name: Unique tool name (snake_case).
            description: What the tool does (shown to LLM).
            parameters: Parameter schema (JSON Schema properties format).
            required: List of required parameter names.
            category: Tool category for grouping.
        """
        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered — overwriting")

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            required_params=required or list(parameters.keys()),
            category=category,
        )
        logger.debug(f"Registered tool: {name} ({category})")

    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool definition by name."""
        return self._tools.get(name)

    def get_tool_definitions(self, category: str | None = None) -> list[dict[str, Any]]:
        """Get all tool definitions in OpenAI function-calling format.

        Args:
            category: If provided, filter to only this category.

        Returns:
            List of tool definitions ready to pass to LLM.
        """
        tools = self._tools.values()
        if category:
            tools = [t for t in tools if t.category == category]

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": tool.required_params,
                    },
                },
            }
            for tool in tools
        ]

    def validate_call(self, name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
        """Validate a tool call before execution.

        Returns:
            (is_valid, error_message) tuple.
        """
        tool = self._tools.get(name)
        if not tool:
            return False, f"Unknown tool: '{name}'"

        # Check required parameters
        for param in tool.required_params:
            if param not in arguments:
                return False, f"Missing required parameter: '{param}' for tool '{name}'"

        return True, ""

    @property
    def tool_names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)
