"""Tool router — classifies requests and selects minimal tool bundles.

Default: no tools. Tools only attach when the request actually needs them.
Routing is heuristic-first, cheap model fallback only if uncertain.

Routes:
  direct_answer  → no tools (default, cheapest path)
  memory_lookup  → memory search only
  web_lookup     → web search only
  file_lookup    → file read + search
  code_work      → file + shell
  multi_tool     → minimal combination
"""
import re
from typing import Optional

from desktop_app.utils.logger import get_logger

logger = get_logger()

# ── Routes ────────────────────────────────────────────────────

ROUTE_DIRECT = "direct_answer"
ROUTE_MEMORY = "memory_lookup"
ROUTE_WEB = "web_lookup"
ROUTE_FILE = "file_lookup"
ROUTE_CODE = "code_work"
ROUTE_MULTI = "multi_tool"

# ── Heuristic Patterns ───────────────────────────────────────

_WEB_PATTERNS = re.compile(
    r"search\s+(?:the\s+)?(?:web|online|internet)|"
    r"(?:latest|current|recent)\s+(?:news|price|update|version|release)|"
    r"what(?:'s| is)\s+happening|look\s*up|google|"
    r"(?:find|check)\s+(?:online|on the web)",
    re.IGNORECASE,
)
_MEMORY_PATTERNS = re.compile(
    r"(?:do you )?remember|recall|what did (?:I|we) (?:say|discuss|talk)|"
    r"earlier (?:we|I|you)|my preference|you told me|"
    r"last (?:time|session|conversation)|from before",
    re.IGNORECASE,
)
_FILE_PATTERNS = re.compile(
    r"(?:read|open|show|cat|view|display)\s+(?:the\s+)?(?:file|contents)|"
    r"(?:/[\w./]+\.\w+)|"  # path-like: /foo/bar.txt
    r"(?:~/[\w./]+)|"      # home path: ~/foo
    r"what(?:'s| is) in (?:the )?file",
    re.IGNORECASE,
)
_CODE_PATTERNS = re.compile(
    r"\b(?:run|execute|build|compile|test|debug|deploy|install|pip|npm|yarn|cargo|make)\b|"
    r"(?:write|create|edit|modify|update|fix)\s+(?:the\s+)?(?:code|script|file|function|class)|"
    r"(?:error|traceback|exception|stack\s*trace|segfault)|"
    r"(?:\.py|\.js|\.ts|\.rs|\.go|\.sh|\.cpp|\.c|\.java)\b",
    re.IGNORECASE,
)


def classify_tool_need(message: str) -> str:
    """Classify a user message into a tool route using heuristics.

    Returns one of: direct_answer, memory_lookup, web_lookup,
    file_lookup, code_work, multi_tool
    """
    msg = message.strip()

    # Count how many categories match
    hits = []
    if _WEB_PATTERNS.search(msg):
        hits.append(ROUTE_WEB)
    if _MEMORY_PATTERNS.search(msg):
        hits.append(ROUTE_MEMORY)
    if _FILE_PATTERNS.search(msg):
        hits.append(ROUTE_FILE)
    if _CODE_PATTERNS.search(msg):
        hits.append(ROUTE_CODE)

    if len(hits) == 0:
        route = ROUTE_DIRECT
    elif len(hits) == 1:
        route = hits[0]
    else:
        route = ROUTE_MULTI

    logger.info(f"[router] '{msg[:60]}...' -> {route}")
    return route


# ── Tool Definitions (Anthropic format) ──────────────────────

TOOL_WEB_SEARCH = {
    "name": "web_search",
    "description": "Search the web for current information, news, or documentation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
        },
        "required": ["query"],
    },
}

TOOL_MEMORY_SEARCH = {
    "name": "memory_search",
    "description": "Search user's persistent memories for relevant past context.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for in memory"},
        },
        "required": ["query"],
    },
}

TOOL_FILE_READ = {
    "name": "file_read",
    "description": "Read the contents of a file at the given path.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute file path"},
        },
        "required": ["path"],
    },
}

TOOL_FILE_SEARCH = {
    "name": "file_search",
    "description": "Search for files matching a pattern or containing text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern or search text"},
            "directory": {"type": "string", "description": "Directory to search in", "default": "."},
        },
        "required": ["pattern"],
    },
}

TOOL_SHELL_EXEC = {
    "name": "shell_exec",
    "description": "Execute a shell command. Use for builds, tests, installs, system checks.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute"},
            "working_dir": {"type": "string", "description": "Working directory", "default": "~"},
        },
        "required": ["command"],
    },
}

TOOL_FILE_WRITE = {
    "name": "file_write",
    "description": "Write content to a file. Creates parent directories if needed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute file path"},
            "content": {"type": "string", "description": "File content to write"},
        },
        "required": ["path", "content"],
    },
}


# ── Tool Bundles ──────────────────────────────────────────────

BUNDLES = {
    ROUTE_DIRECT: [],
    ROUTE_MEMORY: [TOOL_MEMORY_SEARCH],
    ROUTE_WEB:    [TOOL_WEB_SEARCH],
    ROUTE_FILE:   [TOOL_FILE_READ, TOOL_FILE_SEARCH],
    ROUTE_CODE:   [TOOL_FILE_READ, TOOL_FILE_WRITE, TOOL_SHELL_EXEC],
    ROUTE_MULTI:  [TOOL_FILE_READ, TOOL_FILE_SEARCH, TOOL_SHELL_EXEC, TOOL_WEB_SEARCH],
}


def select_tool_bundle(route: str) -> list:
    """Return the minimal tool list for the given route."""
    bundle = BUNDLES.get(route, [])
    names = [t["name"] for t in bundle]
    logger.info(f"[router] bundle for '{route}': {names or 'none'}")
    return bundle
