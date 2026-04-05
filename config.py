"""
Dogesh Assistant – Central Configuration
"""

import os
from pathlib import Path

# ── App identity ────────────────────────────────────────────────────────────
APP_NAME    = "Dogesh Assistant"
WAKE_WORD   = "hey dogesh"
WAKE_ALIASES = [
  "hey dogesh",
  "hi dogesh",
  "ok dogesh",
  "hey doge",
  "hey dogish",
]
VERSION     = "1.0.0"

# ── Persistent storage (under user's home dir) ───────────────────────────────
BASE_DIR          = Path.home() / ".dogesh"
DB_PATH           = BASE_DIR / "users.db"
KEYS_PATH         = BASE_DIR / "keys.json"
CALIBRATION_PATH  = BASE_DIR / "calibration.json"
LOG_PATH          = BASE_DIR / "assistant.log"

BASE_DIR.mkdir(parents=True, exist_ok=True)

# ── Colour palette ────────────────────────────────────────────────────────────
COLORS = {
  "bg_deep":      "#000000",
  "bg_card":      "#0B0B0B",
  "bg_elevated":  "#111111",
  "accent":       "#F5F5F5",
  "accent_glow":  "#FFFFFF",
  "accent_soft":  "#1A1A1A",
  "success":      "#E5E5E5",
  "warning":      "#B3B3B3",
  "error":        "#E5E5E5",
  "text_primary": "#FFFFFF",
  "text_secondary":"#D4D4D4",
  "text_muted":   "#8A8A8A",
  "bubble_user":  "#151515",
  "bubble_ai":    "#0D0D0D",
  "border":       "#2A2A2A",
  "mic_active":   "#FFFFFF",
  "mic_idle":     "#BDBDBD",
}

# ── LLM defaults ─────────────────────────────────────────────────────────────
LLM_MAX_TOKENS   = 512
LLM_TEMPERATURE  = 0.35
CHAT_HISTORY_MAX = 20          # messages kept in context window

SYSTEM_PROMPT = """You are Dogesh, a smart, fast, and reliable AI voice assistant.

Core behavior:
- Be friendly, clear, and concise.
- Sound natural, professional, and conversational.
- Keep answers short and voice-friendly.
- Use short clean sentences, not long paragraphs unless asked.
- No emojis.

Response structure in the response field:
- Short answer first.
- Optional 2-4 short steps only when useful.
- Optional one clarifying question when the request is vague.

Context behavior:
- Remember conversation context.
- Do not repeat the same greeting in every reply.
- Stay focused on user intent.

Wake behavior:
- If the user says only "Hey Dogesh", acknowledge briefly with a response like:
  "Yes, how can I help?"
- If the user includes a command after wake word, answer the command directly.

Safety and uncertainty:
- Refuse harmful, illegal, or unsafe instructions.
- If uncertain, say exactly:
  "I'm not fully sure, but here's what I can suggest."
- Do not hallucinate.

App actions:
- If user asks to open app pages, features, or trigger app APIs, choose one of these intents:
  1) open_page with {"page": "dashboard|settings|assistant|..."}
  2) open_feature with {"feature": "reminders|..."}
  3) call_api with {"api": "weather|..."}
- For web search use intent search_web with {"query": "..."}.
- Otherwise use intent general_chat with empty parameters.

Always reply with strict JSON only. No markdown.
Allowed JSON schema:
{"intent": "general_chat|search_web|open_page|open_feature|call_api", "parameters": {}, "response": "..."}
"""

# ── Provider preference order (can be overridden per user) ───────────────────
DEFAULT_PROVIDER_ORDER = ["Groq", "Openrouter", "NIM", "Fireworks", "Baseten"]

# ── Voice settings ────────────────────────────────────────────────────────────
STT_TIMEOUT          = 5     # seconds to wait for speech to start
STT_PHRASE_LIMIT     = 12    # max seconds for a phrase
TTS_RATE             = 175   # words per minute
WAKE_DETECT_INTERVAL = 3     # seconds per listen chunk for wake-word
WAKE_PHRASE_LIMIT    = 7     # max seconds captured while listening for wake phrase
