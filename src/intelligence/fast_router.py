"""
Fast Router - Bypasses LLM for common commands using pattern matching.
Supports both single-step and multi-step patterns.
Reduces response time from 60s to <1s for recognized instructions.
"""
import re


PATTERNS = [
    (r"(?:create|make|new)\s+(?:a\s+)?folder\s+(?:called\s+|named\s+)?(.+?)\s+(?:in|inside|at)\s+(?:my\s+)?(.+)",
     "create_folder", lambda m: {"path": "~/" + m.group(2).strip() + "/" + m.group(1).strip()}),
    (r"(?:create|make|new)\s+(?:a\s+)?folder\s+(?:called\s+|named\s+)?(.+?)$",
     "create_folder", lambda m: {"path": "~/Documents/" + m.group(1).strip()}),
    (r"(?:open|launch|start|run)\s+(.+)",
     "open_application", lambda m: {"app_name": m.group(1).strip().lower()}),
    (r"(?:organize|sort|clean)\s+(?:my\s+)?(?:downloads|download folder)",
     "SPECIAL_ORGANIZE", lambda m: {}),
    (r"(?:status|health|system status)",
     "get_system_status", lambda m: {}),
    (r"(?:read|show|display|cat|print)\s+(?:the\s+)?(?:file\s+)?(.+?\.\w+)(?:\s+(?:in|from)\s+(?:my\s+)?(.+))?$",
     "read_file_content", lambda m: {"path": ("~/" + m.group(2).strip() + "/" if m.group(2) else "") + m.group(1).strip()}),
    (r"(?:search|find|look for|grep)\s+[\"']?(.+?)[\"']?\s+(?:in|inside|within)\s+(?:the\s+)?(?:file\s+)?(.+?\.\w+)",
     "search_in_file", lambda m: {"path": m.group(2).strip(), "query": m.group(1).strip()}),
    (r"(?:list|show|what.s in|what is in)\s+(?:the\s+)?(?:files\s+in\s+)?(?:my\s+)?(.+?)(?:\s+folder)?$",
     "list_directory", lambda m: {"path": "~/" + m.group(1).strip()}),
    (r"(?:write|save)\s+[\"'](.+?)['\"]\s+(?:to|into)\s+(?:a\s+)?(?:file\s+)?(?:called\s+|named\s+)?(.+)",
     "write_file", lambda m: {"path": m.group(2).strip(), "content": m.group(1).strip()}),
    (r"(?:search|google|look up|find online|search the web for|search for)\s+(.+)",
     "web_search", lambda m: {"query": m.group(1).strip()}),
    (r"(?:fetch|get|open url|read url|read page)\s+(https?://\S+)",
     "fetch_url", lambda m: {"url": m.group(1).strip()}),
]


MULTI_STEP_PATTERNS = [
    # Create a project with full scaffold
    (r"(?:create|make|set up|setup)\s+(?:a\s+)?project\s+(?:called\s+|named\s+)?(.+?)(?:\s+in\s+(?:my\s+)?(.+))?$",
     lambda m: _project_scaffold(m.group(1).strip(), m.group(2))),

    # Create a note with content
    (r"(?:create|make)\s+(?:a\s+)?note\s+(?:called\s+|named\s+)?(.+?)\s+(?:with|containing|that says)\s+(.+)",
     lambda m: [
         {"tool": "create_folder", "arguments": {"path": "~/Documents/Notes"}},
         {"tool": "write_file", "arguments": {"path": "~/Documents/Notes/" + m.group(1).strip(), "content": m.group(2).strip()}},
     ]),

    # Create a file with content in a specific location
    (r"(?:create|write|make)\s+(?:a\s+)?file\s+(?:called\s+|named\s+)?(.+?)\s+(?:in|inside)\s+(?:my\s+)?(.+?)\s+(?:with|containing|that says)\s+(.+)",
     lambda m: [
         {"tool": "write_file", "arguments": {"path": "~/" + m.group(2).strip() + "/" + m.group(1).strip(), "content": m.group(3).strip()}},
     ]),
]


def _project_scaffold(name, location):
    """Generate multi-step plan for project creation."""
    base = "~/" + (location.strip() if location else "Documents") + "/" + name
    return [
        {"tool": "create_folder", "arguments": {"path": base}},
        {"tool": "create_folder", "arguments": {"path": base + "/src"}},
        {"tool": "create_folder", "arguments": {"path": base + "/docs"}},
        {"tool": "create_folder", "arguments": {"path": base + "/tests"}},
        {"tool": "create_folder", "arguments": {"path": base + "/data"}},
        {"tool": "write_file", "arguments": {"path": base + "/README.md", "content": "# " + name + "\n\nProject created by MACAL Agent.\n"}},
    ]


def fast_route(instruction):
    """Try to match instruction to a single-step pattern.
    Returns: (tool_name, arguments) if matched, None if LLM needed.
    """
    text = instruction.strip()
    for pattern, tool, arg_builder in PATTERNS:
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            return (tool, arg_builder(match))
    return None


def fast_route_multi(instruction):
    """Try to match instruction to a multi-step pattern.
    Returns: list of {"tool": ..., "arguments": ...} or None.
    """
    text = instruction.strip()
    for pattern, step_builder in MULTI_STEP_PATTERNS:
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            return step_builder(match)
    return None
