"""Tool executor — handles tool calls returned by the model.

Each tool has a real implementation. Tools are only invoked when the model
explicitly requests them via tool_use blocks in its response.
"""
import subprocess
from pathlib import Path
from typing import Dict

from desktop_app.utils.logger import get_logger

logger = get_logger()

MAX_OUTPUT = 4000  # Truncate tool output to limit token cost


def execute_tool_call(name: str, arguments: Dict, supabase=None) -> str:
    """Execute a single tool call. Returns result string."""
    logger.info(f"[tool] executing: {name}({list(arguments.keys())})")

    try:
        if name == "shell_exec":
            return _exec_shell(arguments)
        elif name == "file_read":
            return _exec_file_read(arguments)
        elif name == "file_write":
            return _exec_file_write(arguments)
        elif name == "file_search":
            return _exec_file_search(arguments)
        elif name == "web_search":
            return _exec_web_search(arguments)
        elif name == "memory_search":
            return _exec_memory_search(arguments, supabase)
        else:
            return f"[Unknown tool: {name}]"
    except Exception as e:
        logger.error(f"[tool] {name} failed: {e}")
        return f"[Tool error: {e}]"


def _exec_shell(args: Dict) -> str:
    cmd = args.get("command", "")
    cwd = args.get("working_dir", str(Path.home()))
    if not cmd:
        return "[No command provided]"
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, cwd=cwd,
        )
        out = r.stdout
        if r.stderr:
            out += f"\n[stderr] {r.stderr}"
        if r.returncode != 0:
            out += f"\n[exit code {r.returncode}]"
        return (out.strip() or "(no output)")[:MAX_OUTPUT]
    except subprocess.TimeoutExpired:
        return "[Timed out after 30s]"


def _exec_file_read(args: Dict) -> str:
    path = args.get("path", "")
    if not path:
        return "[No path provided]"
    p = Path(path).expanduser()
    if not p.exists():
        return f"[Not found: {path}]"
    size = p.stat().st_size
    if size > 200_000:
        content = p.read_text(errors="replace")[:5000]
        return f"[File too large ({size}B), showing first 5000 chars]\n{content}"
    return p.read_text(errors="replace")[:MAX_OUTPUT]


def _exec_file_write(args: Dict) -> str:
    path = args.get("path", "")
    content = args.get("content", "")
    if not path:
        return "[No path provided]"
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"[Wrote {len(content)} bytes to {path}]"


def _exec_file_search(args: Dict) -> str:
    pattern = args.get("pattern", "")
    directory = args.get("directory", ".")
    if not pattern:
        return "[No pattern provided]"
    p = Path(directory).expanduser()
    if not p.exists():
        return f"[Directory not found: {directory}]"
    matches = sorted(p.rglob(pattern))[:50]
    if not matches:
        return f"[No files matching '{pattern}' in {directory}]"
    lines = [str(m) for m in matches]
    return "\n".join(lines)[:MAX_OUTPUT]


def _exec_web_search(args: Dict) -> str:
    query = args.get("query", "")
    if not query:
        return "[No query provided]"
    # Placeholder — real implementation needs a search API
    return f"[Web search not yet implemented. Query: {query}]"


def _exec_memory_search(args: Dict, supabase=None) -> str:
    query = args.get("query", "")
    if not query:
        return "[No query provided]"
    if not supabase or not supabase.available:
        return "[Memory search unavailable — Supabase not configured]"
    memories = supabase.get_memories(limit=10)
    if not memories:
        return "[No memories stored yet]"
    # Simple keyword match for now
    q_lower = query.lower()
    relevant = [m for m in memories if q_lower in m.get("content", "").lower()]
    if not relevant:
        relevant = memories[:5]
    lines = [f"- {m.get('content', '')}" for m in relevant[:6]]
    return "\n".join(lines) or "[No relevant memories found]"
