"""
Dogesh Assistant – Centralised Application State
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable
from enum import Enum


class AssistantStatus(str, Enum):
    IDLE      = "idle"
    WAKE      = "listening_wake"
    LISTENING = "listening_command"
    THINKING  = "thinking"
    SPEAKING  = "speaking"
    ERROR     = "error"


@dataclass
class ChatMessage:
    role: str          # "user" | "assistant"
    content: str
    timestamp: str = ""
    avatar: str = ""


@dataclass
class AppState:
    # ── Auth ──────────────────────────────────────────────────────────────────
    current_user: Optional[dict] = None
    is_logged_in: bool = False

    # ── Assistant ─────────────────────────────────────────────────────────────
    status: AssistantStatus = AssistantStatus.IDLE
    chat_history: List[ChatMessage] = field(default_factory=list)
    current_transcript: str = ""

    # ── Voice ─────────────────────────────────────────────────────────────────
    wake_word_active: bool = False
    mic_available: bool = False

    # ── Keys ──────────────────────────────────────────────────────────────────
    api_keys: dict = field(default_factory=dict)
    active_provider: Optional[str] = None
    user_avatar: str = ""

    # ── Callbacks (set by UI) ─────────────────────────────────────────────────
    on_status_change: Optional[Callable] = None
    on_new_message:   Optional[Callable] = None
    on_transcript:    Optional[Callable] = None

    # ── Helpers ───────────────────────────────────────────────────────────────
    def set_status(self, s: AssistantStatus):
        self.status = s
        if self.on_status_change:
            self.on_status_change(s)

    def add_message(self, role: str, content: str, avatar: str = "", notify: bool = True):
        import datetime
        msg = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.datetime.now().strftime("%H:%M"),
            avatar=avatar,
        )
        self.chat_history.append(msg)
        if notify and self.on_new_message:
            self.on_new_message(msg)

    def set_transcript(self, text: str):
        self.current_transcript = text
        if self.on_transcript:
            self.on_transcript(text)

    def clear_history(self):
        self.chat_history.clear()

    def login(self, user: dict):
        self.current_user = user
        self.is_logged_in = True
        self.user_avatar = user.get("avatar", "")

    def logout(self):
        self.current_user = None
        self.is_logged_in = False
        self.chat_history.clear()
        self.api_keys = {}
        self.active_provider = None
        self.wake_word_active = False
        self.user_avatar = ""
