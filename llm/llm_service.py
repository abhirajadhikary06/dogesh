"""
Dogesh Assistant – LLM Service
Strict backend: llmsays (PyPI). Falls back to direct OpenAI-compat call only
when llmsays itself is unavailable (e.g. disk-space constraints at install time).
"""

import os
import json
import re
from typing import List, Optional

from config import (
    SYSTEM_PROMPT,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    CHAT_HISTORY_MAX,
    DEFAULT_PROVIDER_ORDER,
)


# ── Attempt to import llmsays ─────────────────────────────────────────────────
try:
    from llmsays import llmsays as _llmsays_call
    _LLMSAYS_AVAILABLE = True
except ImportError:
    _LLMSAYS_AVAILABLE = False


class LLMService:
    """
    Manages chat history and sends prompts via the llmsays backend.

    llmsays auto-selects:
      • Provider  – whichever has a valid env-var key and lowest latency
      • Model tier – small / medium / large / extra_large based on query complexity
    """

    def __init__(self, api_keys: dict, provider_preference: Optional[List[str]] = None):
        """
        api_keys: {"GROQ_API_KEY": "gsk_...", "OPENROUTER_API_KEY": "sk-or-...", ...}
        provider_preference: ordered list, e.g. ["Groq", "Openrouter"]
        """
        self.api_keys = api_keys
        self.provider_preference = provider_preference or DEFAULT_PROVIDER_ORDER
        self._history: List[dict] = []          # {"role": "user"|"assistant", "content": str}
        self._apply_env_keys()

    # ── Public ────────────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> dict:
        """
        Send a user message; return structured dict:
          {
            "intent": "general_chat" | "search_web",
            "parameters": {...},
            "response": "<text to speak / display>"
          }
        """
        self._history.append({"role": "user", "content": user_message})
        self._trim_history()

        prompt = self._build_prompt(user_message)

        try:
            raw = self._query_llm(prompt)
            result = self._parse_response(raw)
        except Exception as exc:
            result = {
                "intent": "general_chat",
                "parameters": {},
                "response": f"Sorry, I hit an error: {exc}",
            }

        self._history.append({"role": "assistant", "content": result["response"]})
        return result

    def reset(self):
        self._history.clear()

    def update_keys(self, api_keys: dict):
        self.api_keys = api_keys
        self._apply_env_keys()

    # ── Private ───────────────────────────────────────────────────────────────

    def _apply_env_keys(self):
        """Inject keys into environment variables so llmsays can discover them."""
        key_map = {
            "GROQ_API_KEY":       "GROQ_API_KEY",
            "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
            "NIVIDIA_API_KEY":    "NIVIDIA_API_KEY",
            "NVIDIA_API_KEY":     "NVIDIA_API_KEY",
            "FIREWORKSAI_API_KEY":"FIREWORKSAI_API_KEY",
            "BASETEN_API_KEY":    "BASETEN_API_KEY",
        }
        for env_key, stored_key in key_map.items():
            value = self.api_keys.get(stored_key) or self.api_keys.get(env_key)
            if value:
                os.environ[env_key] = value

    def _build_prompt(self, user_message: str) -> str:
        """
        llmsays accepts a single string prompt.
        We embed system instruction + trimmed history + new message.
        """
        parts = [SYSTEM_PROMPT, ""]

        # Include up to CHAT_HISTORY_MAX-1 prior exchanges
        for turn in self._history[:-1]:          # exclude latest user msg (appended above)
            role_label = "User" if turn["role"] == "user" else "Dogesh"
            parts.append(f"{role_label}: {turn['content']}")

        parts.append(f"\nUser's new message: {user_message}")
        parts.append("Dogesh (JSON only):")
        return "\n".join(parts)

    def _query_llm(self, prompt: str) -> str:
        if _LLMSAYS_AVAILABLE:
            return _llmsays_call(
                query=prompt,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
                provider_preference=self.provider_preference,
                use_multiprocessing=False,
            )
        # ── Fallback: direct OpenAI-compat call (Groq endpoint) ──────────────
        return self._fallback_call(prompt)

    def _fallback_call(self, prompt: str) -> str:
        """
        Direct call to the first available provider using the openai SDK.
        Used only when llmsays package is not installed.
        """
        from openai import OpenAI

        providers_cfg = [
            {
                "name": "Groq",
                "base_url": "https://api.groq.com/openai/v1",
                "env_key": "GROQ_API_KEY",
                "model": "llama-3.3-70b-versatile",
            },
            {
                "name": "Openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "env_key": "OPENROUTER_API_KEY",
                "model": "google/gemini-3-flash-preview",
            },
            {
                "name": "NIM",
                "base_url": "https://integrate.api.nvidia.com/v1",
                "env_key": "NIVIDIA_API_KEY",
                "model": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
            },
            {
                "name": "Fireworks",
                "base_url": "https://api.fireworks.ai/inference/v1",
                "env_key": "FIREWORKSAI_API_KEY",
                "model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
            },
            {
                "name": "Baseten",
                "base_url": "https://inference.baseten.co/v1",
                "env_key": "BASETEN_API_KEY",
                "model": "moonshotai/Kimi-K2.5",
            },
        ]

        # Honour provider_preference order
        ordered = sorted(
            providers_cfg,
            key=lambda p: (
                self.provider_preference.index(p["name"])
                if p["name"] in self.provider_preference
                else 99
            ),
        )

        errors = []
        for cfg in ordered:
            api_key = os.getenv(cfg["env_key"])
            if not api_key:
                continue
            try:
                client = OpenAI(base_url=cfg["base_url"], api_key=api_key)
                resp = client.chat.completions.create(
                    model=cfg["model"],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=LLM_MAX_TOKENS,
                    temperature=LLM_TEMPERATURE,
                )
                content = resp.choices[0].message.content or ""
                return content.strip()
            except Exception as e:
                errors.append(f"{cfg['name']}: {e}")

        raise RuntimeError("All providers failed: " + " | ".join(errors))

    def _parse_response(self, raw: str) -> dict:
        """Extract JSON from LLM output. Fall back to plain-text chat."""
        # Try to find JSON block
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                # Validate required keys
                if "intent" in data and "response" in data:
                    data.setdefault("parameters", {})
                    return data
            except json.JSONDecodeError:
                pass

        # Plain-text fallback
        return {
            "intent": "general_chat",
            "parameters": {},
            "response": raw.strip() or "I didn't get a good response. Please try again.",
        }

    def _trim_history(self):
        if len(self._history) > CHAT_HISTORY_MAX:
            self._history = self._history[-CHAT_HISTORY_MAX:]
