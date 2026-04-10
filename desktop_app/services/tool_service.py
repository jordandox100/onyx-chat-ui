"""Tool service — gives ONYX filesystem and shell access"""
import subprocess
import re
from pathlib import Path

from desktop_app.utils.logger import get_logger

logger = get_logger()

TOOLS_SYSTEM_PROMPT = """
You have direct access to the user's computer through tools. Use them when asked to build, check, fix, or explore anything.

Available tools — wrap each call in XML tags exactly as shown:

1. Run a shell command:
<tool_call type="shell">
command here
</tool_call>

2. Read a file:
<tool_call type="read_file">
/absolute/path/to/file
</tool_call>

3. Write or create a file:
<tool_call type="write_file" path="/absolute/path/to/file">
file content here
</tool_call>

4. List directory contents:
<tool_call type="list_dir">
/absolute/path/to/directory
</tool_call>

Rules:
- You may use multiple tool calls in one response.
- After tools execute you receive results and can continue.
- Always explain what you are about to do before executing destructive commands.
- Prefer absolute paths.
"""

TOOL_PATTERN = re.compile(
    r'<tool_call\s+type="(\w+)"(?:\s+path="([^"]*)")?\s*>(.*?)</tool_call>',
    re.DOTALL,
)


class ToolService:
    def __init__(self, working_dir=None):
        self.working_dir = working_dir or str(Path.home())

    def get_tools_prompt(self) -> str:
        return TOOLS_SYSTEM_PROMPT

    def parse_tool_calls(self, text: str) -> list:
        calls = []
        for m in TOOL_PATTERN.finditer(text):
            calls.append({
                "type": m.group(1),
                "path": m.group(2),
                "content": m.group(3).strip(),
                "full_match": m.group(0),
            })
        return calls

    def execute(self, call: dict) -> str:
        t = call["type"]
        if t == "shell":
            return self.run_shell(call["content"])
        elif t == "read_file":
            return self.read_file(call["content"])
        elif t == "write_file":
            return self.write_file(call["path"] or "", call["content"])
        elif t == "list_dir":
            return self.list_dir(call["content"])
        return f"Unknown tool: {t}"

    def run_shell(self, command: str) -> str:
        try:
            r = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=30, cwd=self.working_dir,
            )
            out = r.stdout
            if r.stderr:
                out += f"\n[stderr] {r.stderr}"
            if r.returncode != 0:
                out += f"\n[exit code {r.returncode}]"
            return out.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return "[timed out after 30s]"
        except Exception as e:
            return f"[error] {e}"

    def read_file(self, path: str) -> str:
        try:
            p = Path(path.strip())
            if not p.exists():
                return f"[not found: {path}]"
            size = p.stat().st_size
            if size > 200_000:
                return f"[file too large: {size} bytes — showing first 5000 chars]\n{p.read_text(errors='replace')[:5000]}"
            return p.read_text(errors="replace")
        except Exception as e:
            return f"[error] {e}"

    def write_file(self, path: str, content: str) -> str:
        try:
            p = Path(path.strip())
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return f"[wrote {len(content)} bytes to {path}]"
        except Exception as e:
            return f"[error] {e}"

    def list_dir(self, path: str) -> str:
        try:
            p = Path(path.strip())
            if not p.exists():
                return f"[not found: {path}]"
            entries = sorted(p.iterdir())
            lines = []
            for e in entries[:200]:
                kind = "d" if e.is_dir() else "f"
                sz = "" if e.is_dir() else f"  ({e.stat().st_size}b)"
                lines.append(f"{kind} {e.name}{sz}")
            if len(entries) > 200:
                lines.append(f"... +{len(entries) - 200} more")
            return "\n".join(lines) or "(empty directory)"
        except Exception as e:
            return f"[error] {e}"

    @staticmethod
    def strip_tool_tags(text: str) -> str:
        """Remove tool_call XML from response for clean display."""
        return TOOL_PATTERN.sub("", text).strip()
