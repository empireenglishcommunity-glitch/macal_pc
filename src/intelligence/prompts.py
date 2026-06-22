"""
Prompt Templates — System prompts and instruction templates for the agent.

All prompts are defined here (not scattered in code) for easy iteration
and testing. Each prompt is a function that accepts context parameters
and returns the final prompt string.
"""

from __future__ import annotations


def agent_system_prompt() -> str:
    """Core system prompt defining the agent's role and behavior rules."""
    return """You are MACAL Agent, a professional AI assistant that manages and automates a Windows 11 desktop environment.

ROLE:
- You execute tasks by calling tools (functions) with precise parameters.
- You plan multi-step tasks by breaking them into sequential tool calls.
- You ALWAYS use tools to take actions — never just describe what should be done.

RULES:
1. Only call tools that are available in your tool list.
2. Use exact file paths (expand ~ to the user's home directory).
3. For destructive operations (delete, overwrite), flag them clearly.
4. If a task is ambiguous, ask for clarification before acting.
5. After completing a task, summarize what was done.
6. If a step fails, stop and report the error — do not guess alternatives.

OUTPUT FORMAT:
- When calling tools, respond with a valid JSON tool_call.
- When reporting results, use clear structured text.
- Never fabricate file paths or folder names that don't exist."""


def file_classification_prompt(filename: str, metadata: str, content_preview: str = "") -> str:
    """Prompt for AI-powered file classification."""
    return f"""Classify this file into the appropriate category. Return ONLY valid JSON.

FILE INFORMATION:
- Filename: {filename}
- Metadata: {metadata}
{f'- Content preview: {content_preview[:1500]}' if content_preview else ''}

RESPOND WITH THIS EXACT JSON STRUCTURE:
{{
    "category": "Documents|Code|Images|Videos|Audio|Archives|Data|Other",
    "subcategory": "specific type within category",
    "suggested_name": "descriptive_filename_without_extension",
    "date": "YYYY-MM or unknown",
    "confidence": 0.0 to 1.0
}}

Be precise. Use the content and filename to determine the best category."""


def task_planning_prompt(instruction: str, available_tools: str) -> str:
    """Prompt for decomposing a user instruction into executable steps."""
    return f"""Plan the execution of this task by breaking it into steps.
Each step must be a single tool call.

USER INSTRUCTION: {instruction}

AVAILABLE TOOLS:
{available_tools}

Respond with a JSON array of steps:
[
    {{"step": 1, "tool": "tool_name", "params": {{...}}, "description": "what this does"}},
    {{"step": 2, "tool": "tool_name", "params": {{...}}, "description": "what this does"}}
]

Rules:
- Use ONLY tools from the available list above.
- Each step must be independently executable.
- Order steps logically (create folder before moving files into it).
- Include error-prone steps with a "verify" note.
- Keep the plan minimal — fewest steps to complete the task."""


def gui_action_prompt(task: str, accessibility_tree: str) -> str:
    """Prompt for deciding GUI actions based on accessibility tree state."""
    return f"""You are controlling a Windows desktop application.
Based on the current UI state, decide the NEXT single action to take.

TASK: {task}

CURRENT UI STATE (accessibility tree):
{accessibility_tree}

Respond with exactly ONE action in JSON format:
{{
    "action": "click|type|scroll|hotkey|wait",
    "target": "@element_ref or description",
    "value": "text to type or key combo (if applicable)",
    "reasoning": "why this action"
}}

Rules:
- Only reference elements visible in the accessibility tree above.
- Use @eN references when available (most reliable).
- One action at a time — you'll see the updated state after each action."""
