"""
Dogesh Assistant – Central Configuration
"""

import os
from pathlib import Path

# ── App identity ────────────────────────────────────────────────────────────
APP_NAME    = "Dogesh Assistant"
WAKE_WORD   = "hey dogesh"
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
    "bg_deep":      "#070B14",
    "bg_card":      "#0D1321",
    "bg_elevated":  "#131B2E",
    "accent":       "#4F8EF7",
    "accent_glow":  "#2563EB",
    "accent_soft":  "#1D3461",
    "success":      "#22C55E",
    "warning":      "#F59E0B",
    "error":        "#EF4444",
    "text_primary": "#E8EDF5",
    "text_secondary":"#8A9BB5",
    "text_muted":   "#4A5568",
    "bubble_user":  "#1E40AF",
    "bubble_ai":    "#0F1B30",
    "border":       "#1A2744",
    "mic_active":   "#EF4444",
    "mic_idle":     "#4F8EF7",
}

# ── LLM defaults ─────────────────────────────────────────────────────────────
LLM_MAX_TOKENS   = 512
LLM_TEMPERATURE  = 0.35
CHAT_HISTORY_MAX = 20          # messages kept in context window

SYSTEM_PROMPT = """You are Dogesh, a smart, friendly, and concise voice assistant.
You help users with information, web searches, and everyday tasks.
When the user wants to search the web, reply ONLY with valid JSON:
  {"intent": "search_web", "parameters": {"query": "<exact search query>"},
   "response": "<what you'll say aloud>"}
For all other requests, reply ONLY with valid JSON:
  {"intent": "general_chat", "parameters": {},
   "response": "<your helpful answer — be concise, 1-3 sentences>"}
Always use the JSON format. Never add markdown, bullet lists, or explanations outside the JSON."""

# ── Provider preference order (can be overridden per user) ───────────────────
DEFAULT_PROVIDER_ORDER = ["Groq", "Openrouter", "NIM", "Fireworks", "Baseten"]

# ── Voice settings ────────────────────────────────────────────────────────────
STT_TIMEOUT          = 5     # seconds to wait for speech to start
STT_PHRASE_LIMIT     = 12    # max seconds for a phrase
TTS_RATE             = 175   # words per minute
WAKE_DETECT_INTERVAL = 3     # seconds per listen chunk for wake-word
