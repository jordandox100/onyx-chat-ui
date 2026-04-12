"""ONYX Runtime — Supabase-backed agent with direct Anthropic calls.

No tools by default. Tool bundles attached conditionally per request.
Routing is heuristic-first (zero-cost), cheap model fallback if uncertain.

Normal turn (no tools):
  System (~800 tok): persona + summary + goals + beliefs + memories
  Messages (~3000 tok): last 6 only
  Total: ~4000 tokens

Tool turn (when needed):
  Same context + minimal tool definitions for the selected bundle
"""
import os
import json
from typing import Optional, List, Dict

from desktop_app.services.tool_router import (
    classify_tool_need, select_tool_bundle,
    ROUTE_DIRECT, ROUTE_MULTI,
)
from desktop_app.services.tool_executor import execute_tool_call
from desktop_app.utils.logger import get_logger

logger = get_logger()

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

PERSONA = (
    "You are ONYX, a persistent AI assistant on the user's Linux desktop. "
    "You are sharp, direct, technically savvy, and genuinely helpful. "
    "You have persistent memory across sessions. "
    "Be concise. Solve the real problem."
)

RECENT_WINDOW = 6
SUMMARY_INTERVAL = 8
DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOOL_ROUNDS = 3


class OnyxRuntime:
    """Supabase state + direct Anthropic calls + conditional tool attachment."""

    def __init__(self, supabase=None, storage=None):
        self.supabase = supabase
        self.storage = storage
        self._client = None
        self._model = DEFAULT_MODEL
        self._configured = False
        self._connect()

    def _connect(self):
        if not ANTHROPIC_AVAILABLE:
            logger.warning("anthropic SDK not installed")
            return
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not key:
            logger.warning("ANTHROPIC_API_KEY not set")
            return
        self._client = anthropic.Anthropic(api_key=key)
        self._configured = True
        logger.info("Anthropic client ready")

    @property
    def available(self) -> bool:
        return self._configured and self._client is not None

    @property
    def status(self) -> str:
        if not ANTHROPIC_AVAILABLE:
            return "SDK_MISSING"
        if not self._configured:
            return "NOT_CONFIGURED"
        return "READY"

    @property
    def status_detail(self) -> str:
        if not ANTHROPIC_AVAILABLE:
            return "pip install anthropic"
        if not self._configured:
            return "Set ANTHROPIC_API_KEY in .env"
        return f"Ready — model: {self._model}"

    @property
    def model(self) -> str:
        return self._model

    def set_model(self, model: str):
        self._model = model

    # ── Main Entry ────────────────────────────────────────────

    def send_message(self, text: str, conversation_id: int,
                     user_id: str = "local",
                     local_messages: list = None) -> dict:
        """Route, optionally attach tools, call model, return response."""
        if not self.available:
            return {"response": f"[Runtime not ready: {self.status_detail}]",
                    "route": "error", "tools_used": [], "usage": {}}

        # Step 1: Route the request
        route = classify_tool_need(text)
        tools = select_tool_bundle(route)

        # Step 2: Build compact context
        system = self._build_system_prompt(conversation_id, user_id)
        messages = self._build_messages(conversation_id, text, local_messages)

        logger.info(
            f"[runtime] route={route}, tools={len(tools)}, "
            f"model={self._model}, system={len(system)}c, msgs={len(messages)}"
        )

        # Step 3: Execute
        if not tools:
            result = self._execute_direct(system, messages)
        else:
            result = self._execute_with_tools(system, messages, tools)

        result["route"] = route
        result["tools_used"] = [t["name"] for t in tools]

        # Step 4: Persist
        reply = result.get("response", "")
        if reply:
            self._persist_turn(conversation_id, user_id, text, reply)
            self._maybe_update_summary(conversation_id, user_id)

        return result

    # ── Execution Paths ───────────────────────────────────────

    def _execute_direct(self, system: str, messages: list) -> dict:
        """No-tools path — cheapest possible."""
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=system,
                messages=messages,
            )
            reply = response.content[0].text if response.content else ""
            usage = self._extract_usage(response)
            logger.info(f"[runtime:direct] {len(reply)}c, {usage}")
            return {"response": reply, "usage": usage}
        except Exception as e:
            logger.error(f"[runtime:direct] {e}")
            return {"response": f"[Error: {e}]", "usage": {}}

    def _execute_with_tools(self, system: str, messages: list,
                            tools: list) -> dict:
        """Tool path — minimal bundle, up to MAX_TOOL_ROUNDS iterations."""
        tool_results = []

        for round_num in range(MAX_TOOL_ROUNDS):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=4096,
                    system=system,
                    messages=messages,
                    tools=tools,
                )
            except Exception as e:
                logger.error(f"[runtime:tools] round {round_num}: {e}")
                return {"response": f"[Error: {e}]", "usage": {}}

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Model is done — extract final text
                reply = self._extract_text(response)
                usage = self._extract_usage(response)
                logger.info(
                    f"[runtime:tools] done after {round_num + 1} round(s), "
                    f"{len(tool_results)} tool calls, {usage}"
                )
                return {"response": reply, "usage": usage,
                        "tool_calls": tool_results}

            if response.stop_reason == "tool_use":
                # Process tool calls
                tool_use_blocks = [
                    b for b in response.content
                    if b.type == "tool_use"
                ]
                # Append assistant response (with tool_use blocks) to messages
                messages.append({
                    "role": "assistant",
                    "content": response.content,
                })

                # Execute each tool and build tool_result blocks
                tool_result_content = []
                for block in tool_use_blocks:
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    logger.info(f"[runtime:tools] calling {tool_name}")
                    output = execute_tool_call(
                        tool_name, tool_input, supabase=self.supabase
                    )
                    tool_results.append({
                        "name": tool_name,
                        "arguments": json.dumps(tool_input)[:200],
                        "result": output[:500],
                    })
                    tool_result_content.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": output,
                    })

                messages.append({
                    "role": "user",
                    "content": tool_result_content,
                })
            else:
                # Unexpected stop reason — return what we have
                reply = self._extract_text(response)
                return {"response": reply or "[Unexpected stop]",
                        "usage": self._extract_usage(response),
                        "tool_calls": tool_results}

        # Exhausted rounds
        return {"response": "[Tool execution limit reached]",
                "usage": {}, "tool_calls": tool_results}

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _extract_text(response) -> str:
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    @staticmethod
    def _extract_usage(response) -> dict:
        return {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }

    # ── Prompt Building ───────────────────────────────────────

    def _build_system_prompt(self, conversation_id: int,
                             user_id: str) -> str:
        parts = [PERSONA]
        if not self.supabase or not self.supabase.available:
            return parts[0]

        summary = self._get_summary(conversation_id)
        if summary:
            parts.append(f"\n=== Conversation So Far ===\n{summary}")

        goals = self._get_goals(user_id)
        if goals:
            parts.append("\n=== Active Goals ===\n" + "\n".join(
                f"- [{g.get('status','?')}] {g.get('title','')}"
                for g in goals[:5]
            ))

        beliefs = self._get_beliefs(user_id)
        if beliefs:
            parts.append("\n=== What I Know About You ===\n" + "\n".join(
                f"- {b.get('content','')}" for b in beliefs[:8]
            ))

        memories = self._get_memories(user_id, conversation_id)
        if memories:
            parts.append("\n=== Relevant Memories ===\n" + "\n".join(
                f"- {m.get('content','')}" for m in memories[:6]
            ))

        return "\n".join(parts)

    def _build_messages(self, conversation_id: int, new_text: str,
                        local_messages: list = None) -> list:
        messages = []
        if self.supabase and self.supabase.available:
            recent = self.supabase.get_recent_messages(
                str(conversation_id), limit=RECENT_WINDOW
            )
            for m in recent:
                messages.append({"role": m.get("role", "user"),
                                 "content": m.get("content", "")})
        elif local_messages:
            for m in local_messages[-RECENT_WINDOW:]:
                messages.append({"role": m.get("role", "user"),
                                 "content": m.get("content", "")})
        messages.append({"role": "user", "content": new_text})
        return messages

    # ── Supabase Reads ────────────────────────────────────────

    def _get_summary(self, cid: int) -> str:
        if not self.supabase or not self.supabase.available:
            return ""
        try:
            conv = self.supabase.get_conversation(str(cid))
            return (conv or {}).get("summary", "") or ""
        except Exception:
            return ""

    def _get_goals(self, uid: str) -> list:
        if not self.supabase or not self.supabase.available:
            return []
        try:
            return self.supabase.get_goals(uid)
        except Exception:
            return []

    def _get_beliefs(self, uid: str) -> list:
        if not self.supabase or not self.supabase.available:
            return []
        try:
            return self.supabase.get_beliefs(uid)
        except Exception:
            return []

    def _get_memories(self, uid: str, cid: int) -> list:
        if not self.supabase or not self.supabase.available:
            return []
        try:
            return self.supabase.get_memories(uid, limit=6)
        except Exception:
            return []

    # ── Supabase Writes ───────────────────────────────────────

    def _persist_turn(self, cid: int, uid: str, user_text: str,
                      assistant_text: str):
        if not self.supabase or not self.supabase.available:
            return
        c = str(cid)
        self.supabase.add_message(c, "user", user_text)
        self.supabase.add_message(c, "assistant", assistant_text)

    def _maybe_update_summary(self, cid: int, uid: str):
        if not self.supabase or not self.supabase.available or not self._client:
            return
        c = str(cid)
        count = self.supabase.get_message_count(c)
        if count < SUMMARY_INTERVAL:
            return
        conv = self.supabase.get_conversation(c)
        if not conv:
            return
        existing = conv.get("summary", "") or ""
        if len(existing) > 50 and count < (SUMMARY_INTERVAL * 2):
            return
        recent = self.supabase.get_recent_messages(c, limit=20)
        if not recent:
            return
        transcript = "\n".join(
            f"{m.get('role','?')}: {m.get('content','')[:200]}" for m in recent
        )
        try:
            resp = self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                system="Summarize this conversation in 2-3 sentences. Be factual and concise.",
                messages=[{"role": "user", "content": transcript}],
            )
            summary = resp.content[0].text if resp.content else ""
            if summary:
                self.supabase.update_conversation(c, summary=summary)
                logger.info(f"Summary updated for conv {c}")
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")

    # ── State Accessors (inspector) ───────────────────────────

    def get_agent_state(self) -> dict:
        return {
            "status": self.status, "status_detail": self.status_detail,
            "model": self._model, "runtime": "supabase+anthropic",
            "name": "ONYX",
        }

    def get_conversation_summary(self, cid: int) -> str:
        return self._get_summary(cid)

    def get_goals(self, uid: str = "local") -> list:
        return self._get_goals(uid)

    def get_beliefs(self, uid: str = "local") -> list:
        return self._get_beliefs(uid)

    def get_memories(self, uid: str = "local", limit: int = 10) -> list:
        return self._get_memories(uid, 0)

    def get_tasks(self, uid: str = "local") -> list:
        if self.supabase and self.supabase.available:
            return self.supabase.get_tasks(uid)
        return []

    def get_events(self, uid: str = "local", limit: int = 50) -> list:
        if self.supabase and self.supabase.available:
            return self.supabase.get_events(uid, limit)
        return []

    def get_files(self, uid: str = "local", conversation_id: str = None) -> list:
        if self.supabase and self.supabase.available:
            return self.supabase.get_files(uid, conversation_id)
        return []
