"""
Dogesh Assistant – Flet UI
All pages: Login → Register → Voice Calibration → API Setup → Chat
"""

import flet as ft
import threading
import time
from typing import Optional

from config import APP_NAME, WAKE_WORD, COLORS
from core.app_state import AppState, AssistantStatus, ChatMessage
from database import Database


# ══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS
# ══════════════════════════════════════════════════════════════════════════════

def _card(content, padding=20, radius=16, bgcolor=COLORS["bg_card"], **kw):
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=radius,
        bgcolor=bgcolor,
        **kw,
    )

def _label(text, size=13, color=COLORS["text_secondary"], weight=None, **kw):
    return ft.Text(text, size=size, color=color, weight=weight, **kw)

def _heading(text, size=22, color=COLORS["text_primary"], **kw):
    return ft.Text(text, size=size, color=color, weight=ft.FontWeight.BOLD, **kw)

def _accent_btn(text, on_click, width=None, icon=None, disabled=False):
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        disabled=disabled,
        width=width,
        style=ft.ButtonStyle(
            bgcolor={"": COLORS["accent"], "hovered": "#3B82F6", "disabled": "#1A2744"},
            color={"": "#FFFFFF", "disabled": COLORS["text_muted"]},
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.padding.symmetric(horizontal=24, vertical=14),
            elevation={"": 0, "hovered": 4},
            animation_duration=200,
        ),
    )

def _ghost_btn(text, on_click, color=COLORS["text_secondary"]):
    return ft.TextButton(
        text=text,
        on_click=on_click,
        style=ft.ButtonStyle(
            color={"": color, "hovered": COLORS["accent"]},
        ),
    )

def _input_field(label, password=False, hint="", ref=None, on_submit=None, autofocus=False):
    return ft.TextField(
        label=label,
        password=password,
        hint_text=hint,
        ref=ref,
        on_submit=on_submit,
        autofocus=autofocus,
        can_reveal_password=password,
        border_color=COLORS["border"],
        focused_border_color=COLORS["accent"],
        bgcolor=COLORS["bg_elevated"],
        label_style=ft.TextStyle(color=COLORS["text_secondary"], size=13),
        text_style=ft.TextStyle(color=COLORS["text_primary"], size=15),
        hint_style=ft.TextStyle(color=COLORS["text_muted"], size=13),
        border_radius=12,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )

def _divider():
    return ft.Container(height=1, bgcolor=COLORS["border"], margin=ft.margin.symmetric(vertical=8))

def _status_dot(color=COLORS["success"]):
    return ft.Container(width=8, height=8, border_radius=4, bgcolor=color)


# ══════════════════════════════════════════════════════════════════════════════
# CHAT BUBBLE
# ══════════════════════════════════════════════════════════════════════════════

def _chat_bubble(msg: ChatMessage):
    is_user = msg.role == "user"

    bubble_color = COLORS["bubble_user"] if is_user else COLORS["bubble_ai"]
    align = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
    icon = ft.Icon(
        name=ft.Icons.PERSON_ROUNDED if is_user else ft.Icons.AUTO_AWESOME_ROUNDED,
        color=COLORS["accent"] if is_user else "#22D3EE",
        size=18,
    )

    bubble = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    msg.content,
                    size=14,
                    color=COLORS["text_primary"],
                    selectable=True,
                ),
                ft.Text(
                    msg.timestamp,
                    size=10,
                    color=COLORS["text_muted"],
                    text_align=ft.TextAlign.RIGHT,
                ),
            ],
            spacing=4,
            tight=True,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        border_radius=ft.border_radius.only(
            top_left=16,
            top_right=16,
            bottom_left=4 if is_user else 16,
            bottom_right=16 if is_user else 4,
        ),
        bgcolor=bubble_color,
        border=ft.border.all(1, COLORS["border"]),
        shadow=ft.BoxShadow(blur_radius=8, color="#0000001A", offset=ft.Offset(0, 2)),
        max_width=520,
    )

    avatar = ft.Container(
        content=icon,
        width=34,
        height=34,
        border_radius=17,
        bgcolor=COLORS["bg_elevated"],
        border=ft.border.all(1, COLORS["border"]),
        alignment=ft.alignment.center,
    )

    row_controls = [avatar, ft.Container(width=8), bubble] if not is_user else [bubble, ft.Container(width=8), avatar]

    return ft.Container(
        content=ft.Row(row_controls, alignment=align, tight=True),
        animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
        padding=ft.padding.symmetric(vertical=4, horizontal=8),
    )


# ══════════════════════════════════════════════════════════════════════════════
# WAVEFORM ANIMATION (CSS-style pulsing bars)
# ══════════════════════════════════════════════════════════════════════════════

class WaveformWidget:
    """Animated equaliser bars shown during mic activity."""

    def __init__(self, n_bars=8, color=COLORS["accent"]):
        self._bars = []
        self._n    = n_bars
        self._color = color
        self._anim  = False
        self._thread: Optional[threading.Thread] = None
        self.control = self._build()

    def _build(self):
        heights = [12, 18, 28, 36, 42, 36, 28, 18][:self._n]
        for h in heights:
            bar = ft.Container(
                width=5,
                height=h,
                bgcolor=self._color,
                border_radius=3,
                animate_size=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            )
            self._bars.append(bar)
        return ft.Row(
            self._bars,
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def animate(self, page: ft.Page, active: bool):
        self._anim = active
        if active:
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._loop, args=(page,), daemon=True)
            self._thread.start()
        else:
            self._reset(page)

    def _loop(self, page: ft.Page):
        import math, random
        t = 0.0
        while self._anim:
            for i, bar in enumerate(self._bars):
                bar.height = 10 + 30 * abs(math.sin(t + i * 0.5)) + random.uniform(0, 8)
            try:
                page.update()
            except Exception:
                break
            time.sleep(0.08)
            t += 0.2

    def _reset(self, page: ft.Page):
        base = [12, 18, 28, 36, 42, 36, 28, 18]
        for i, bar in enumerate(self._bars):
            bar.height = base[i % len(base)]
        try:
            page.update()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# PAGE BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

class PageBuilder:
    """Stateless factory for each screen view."""

    def __init__(self, page: ft.Page, state: AppState, db: Database, navigate):
        self.page     = page
        self.state    = state
        self.db       = db
        self.navigate = navigate          # callable(route_name)

    # ─────────────────────────────────────────────────────────────────────────
    # SPLASH / LOGO HEADER
    # ─────────────────────────────────────────────────────────────────────────
    def _logo_header(self, subtitle="Your Personal Voice Assistant"):
        return ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.GRAPHIC_EQ_ROUNDED, color="#FFFFFF", size=28),
                                width=52,
                                height=52,
                                border_radius=16,
                                gradient=ft.LinearGradient(
                                    begin=ft.alignment.top_left,
                                    end=ft.alignment.bottom_right,
                                    colors=[COLORS["accent"], "#7C3AED"],
                                ),
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(width=12),
                            ft.Column(
                                [
                                    ft.Text(APP_NAME, size=24, weight=ft.FontWeight.BOLD,
                                            color=COLORS["text_primary"]),
                                    ft.Text(subtitle, size=12, color=COLORS["text_secondary"]),
                                ],
                                spacing=2,
                                tight=True,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # LOGIN PAGE
    # ─────────────────────────────────────────────────────────────────────────
    def login_page(self):
        username_ref = ft.Ref[ft.TextField]()
        password_ref = ft.Ref[ft.TextField]()
        error_text   = ft.Text("", color=COLORS["error"], size=13)

        def do_login(e):
            error_text.value = ""
            uname = (username_ref.current.value or "").strip()
            pwd   = (password_ref.current.value or "").strip()
            if not uname or not pwd:
                error_text.value = "Please enter username and password."
                self.page.update()
                return
            result = self.db.login(uname, pwd)
            if result["ok"]:
                user = result["user"]
                self.state.login(user)
                keys = self.db.load_keys(uname)
                self.state.api_keys = keys
                # Determine next page
                if not user["calibrated"]:
                    self.navigate("calibration")
                elif not user["api_configured"]:
                    self.navigate("api_setup")
                else:
                    self.navigate("chat")
            else:
                error_text.value = result["error"]
                self.page.update()

        return ft.Container(
            content=ft.Column(
                [
                    self._logo_header(),
                    ft.Container(height=40),
                    _card(
                        ft.Column(
                            [
                                _heading("Welcome Back", size=20),
                                ft.Container(height=4),
                                _label("Sign in to continue"),
                                ft.Container(height=20),
                                _input_field("Username", ref=username_ref, autofocus=True,
                                             on_submit=do_login),
                                ft.Container(height=12),
                                _input_field("Password", password=True, ref=password_ref,
                                             on_submit=do_login),
                                ft.Container(height=6),
                                error_text,
                                ft.Container(height=16),
                                _accent_btn("Sign In", do_login, width=340),
                                ft.Container(height=12),
                                ft.Row(
                                    [
                                        _label("Don't have an account?"),
                                        _ghost_btn("Create one", lambda e: self.navigate("register"),
                                                   color=COLORS["accent"]),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=0,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(horizontal=32, vertical=28),
                        width=400,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.alignment.center,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[COLORS["bg_deep"], "#0A0F1E"],
            ),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # REGISTER PAGE
    # ─────────────────────────────────────────────────────────────────────────
    def register_page(self):
        name_ref     = ft.Ref[ft.TextField]()
        username_ref = ft.Ref[ft.TextField]()
        password_ref = ft.Ref[ft.TextField]()
        error_text   = ft.Text("", color=COLORS["error"], size=13)

        def do_register(e):
            error_text.value = ""
            name  = (name_ref.current.value or "").strip()
            uname = (username_ref.current.value or "").strip()
            pwd   = (password_ref.current.value or "").strip()
            result = self.db.register(uname, pwd, name)
            if result["ok"]:
                login_result = self.db.login(uname, pwd)
                self.state.login(login_result["user"])
                self.navigate("calibration")
            else:
                error_text.value = result["error"]
                self.page.update()

        return ft.Container(
            content=ft.Column(
                [
                    self._logo_header("Create Your Account"),
                    ft.Container(height=36),
                    _card(
                        ft.Column(
                            [
                                _heading("Get Started", size=20),
                                ft.Container(height=4),
                                _label("Set up your personal assistant"),
                                ft.Container(height=20),
                                _input_field("Display Name", ref=name_ref, autofocus=True,
                                             hint="e.g. Alex"),
                                ft.Container(height=12),
                                _input_field("Username (min 3 chars)", ref=username_ref),
                                ft.Container(height=12),
                                _input_field("Password (min 6 chars)", password=True,
                                             ref=password_ref, on_submit=do_register),
                                ft.Container(height=6),
                                error_text,
                                ft.Container(height=16),
                                _accent_btn("Create Account", do_register, width=340),
                                ft.Container(height=12),
                                ft.Row(
                                    [
                                        _label("Already have an account?"),
                                        _ghost_btn("Sign in", lambda e: self.navigate("login"),
                                                   color=COLORS["accent"]),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=0,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(horizontal=32, vertical=28),
                        width=400,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.alignment.center,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[COLORS["bg_deep"], "#0A0F1E"],
            ),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # VOICE CALIBRATION PAGE
    # ─────────────────────────────────────────────────────────────────────────
    def calibration_page(self):
        from voice.stt import STTEngine

        stt = STTEngine()
        status_text     = ft.Text("Press Start to begin calibration", size=14,
                                  color=COLORS["text_secondary"])
        transcript_text = ft.Text("", size=15, color=COLORS["text_primary"],
                                  italic=True, text_align=ft.TextAlign.CENTER)
        progress_ring   = ft.ProgressRing(width=40, height=40, stroke_width=3,
                                          color=COLORS["accent"], visible=False)
        threshold_value = ft.Text("", size=12, color=COLORS["text_muted"])
        waveform        = WaveformWidget(color=COLORS["accent"])
        attempts        = [0]
        calibration_data = {}

        steps = [
            "Say: \"Hey Dogesh, what's the weather?\"",
            "Say: \"Hey Dogesh, search for news today\"",
            "Say: \"Hey Dogesh, set a reminder\"",
        ]
        step_text = ft.Text(steps[0], size=16, weight=ft.FontWeight.W_500,
                            color=COLORS["text_primary"], text_align=ft.TextAlign.CENTER)

        start_btn = ft.Ref[ft.ElevatedButton]()

        def on_progress(msg):
            status_text.value = msg
            self.page.update()

        def run_calibration(_e=None):
            start_btn.current.disabled = True
            progress_ring.visible = True
            waveform.animate(self.page, True)
            status_text.value = "Calibrating microphone…"
            self.page.update()

            threshold = stt.calibrate(duration=2.0, on_progress=on_progress)
            calibration_data["threshold"] = threshold
            threshold_value.value = f"Energy threshold: {threshold:.0f}"

            for i, instruction in enumerate(steps):
                step_text.value = instruction
                status_text.value = f"Recording sample {i+1}/3…"
                self.page.update()
                time.sleep(0.3)
                text = stt.listen_once(timeout=8, phrase_limit=10, on_listening=lambda m: None)
                transcript_text.value = f'Heard: "{text}"' if text else "(no audio detected)"
                self.page.update()
                time.sleep(0.5)

            waveform.animate(self.page, False)
            progress_ring.visible = False
            calibration_data["done"] = True
            status_text.value = "✓ Calibration complete!"
            step_text.value = "Your voice is configured. Tap Continue."
            transcript_text.value = ""
            start_btn.current.disabled = False
            start_btn.current.text = "Re-calibrate"
            continue_btn.disabled = False
            self.page.update()

        def go_continue(_e):
            uname = self.state.current_user["username"]
            self.db.save_calibration(uname, calibration_data)
            self.db.mark_calibrated(uname)
            # Refresh state
            self.state.current_user["calibrated"] = 1
            self.navigate("api_setup")

        continue_btn = ft.ElevatedButton(
            text="Continue →",
            on_click=go_continue,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor={"": COLORS["success"], "disabled": "#1A2744"},
                color={"": "#FFFFFF", "disabled": COLORS["text_muted"]},
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.padding.symmetric(horizontal=28, vertical=14),
            ),
        )

        return ft.Container(
            content=ft.Column(
                [
                    self._logo_header("Voice Calibration"),
                    ft.Container(height=28),
                    _card(
                        ft.Column(
                            [
                                _heading("Set Up Your Voice", size=19),
                                ft.Container(height=4),
                                _label(f'We\'ll calibrate your mic and the wake word "{WAKE_WORD.title()}"'),
                                _divider(),
                                ft.Container(height=12),
                                step_text,
                                ft.Container(height=18),
                                ft.Container(
                                    content=waveform.control,
                                    height=60,
                                    alignment=ft.alignment.center,
                                ),
                                ft.Container(height=12),
                                ft.Row([progress_ring, ft.Container(width=10), status_text],
                                       alignment=ft.MainAxisAlignment.CENTER),
                                ft.Container(height=8),
                                transcript_text,
                                threshold_value,
                                ft.Container(height=20),
                                ft.Row(
                                    [
                                        _accent_btn("▶ Start Calibration",
                                                    lambda e: threading.Thread(
                                                        target=run_calibration, daemon=True).start(),
                                                    ref=start_btn),
                                        ft.Container(width=12),
                                        continue_btn,
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                ft.Container(height=8),
                                _ghost_btn("Skip for now →", lambda e: self.navigate("api_setup"),
                                           color=COLORS["text_muted"]),
                            ],
                            spacing=0,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(horizontal=32, vertical=28),
                        width=480,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.alignment.center,
            bgcolor=COLORS["bg_deep"],
        )

    # ─────────────────────────────────────────────────────────────────────────
    # API SETUP PAGE
    # ─────────────────────────────────────────────────────────────────────────
    def api_setup_page(self):
        providers = [
            ("Groq",        "GROQ_API_KEY",        "gsk_…",      ft.Icons.BOLT_ROUNDED),
            ("OpenRouter",  "OPENROUTER_API_KEY",   "sk-or-v1-…", ft.Icons.HUB_ROUNDED),
            ("NVIDIA NIM",  "NIVIDIA_API_KEY",      "nvapi-…",    ft.Icons.MEMORY_ROUNDED),
            ("Fireworks AI","FIREWORKSAI_API_KEY",  "fw_…",       ft.Icons.WHATSHOT_ROUNDED),
            ("Baseten",     "BASETEN_API_KEY",       "ZCOq…",      ft.Icons.CLOUD_ROUNDED),
        ]

        existing_keys = self.db.load_keys(self.state.current_user["username"])
        refs = {}
        error_text = ft.Text("", color=COLORS["error"], size=13)
        info_text  = ft.Text("Add at least one API key to proceed.", size=13,
                             color=COLORS["text_secondary"])

        def make_provider_row(name, env_key, placeholder, icon):
            ref = ft.Ref[ft.TextField]()
            refs[env_key] = ref
            tf = ft.TextField(
                ref=ref,
                value=existing_keys.get(env_key, ""),
                hint_text=placeholder,
                password=True,
                can_reveal_password=True,
                border_color=COLORS["border"],
                focused_border_color=COLORS["accent"],
                bgcolor=COLORS["bg_elevated"],
                text_style=ft.TextStyle(color=COLORS["text_primary"], size=13),
                hint_style=ft.TextStyle(color=COLORS["text_muted"], size=12),
                border_radius=10,
                content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
                expand=True,
            )
            return ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, color=COLORS["accent"], size=20),
                        width=36,
                        height=36,
                        border_radius=10,
                        bgcolor=COLORS["accent_soft"],
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=10),
                    ft.Column(
                        [
                            ft.Text(name, size=13, weight=ft.FontWeight.W_600,
                                    color=COLORS["text_primary"]),
                            tf,
                        ],
                        spacing=4,
                        tight=True,
                        expand=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        provider_rows = [make_provider_row(*p) for p in providers]

        def save_and_continue(e):
            keys = {}
            for _, env_key, _, _ in providers:
                val = (refs[env_key].current.value or "").strip()
                if val:
                    keys[env_key] = val

            if not keys:
                error_text.value = "Please add at least one API key."
                self.page.update()
                return

            uname = self.state.current_user["username"]
            self.db.save_keys(uname, keys)
            self.db.mark_api_configured(uname)
            self.state.api_keys = keys
            self.state.current_user["api_configured"] = 1
            self.navigate("chat")

        return ft.Container(
            content=ft.Column(
                [
                    self._logo_header("API Configuration"),
                    ft.Container(height=24),
                    _card(
                        ft.Column(
                            [
                                _heading("Connect Your LLM Provider", size=19),
                                ft.Container(height=4),
                                _label("Add at least one API key. Keys are stored locally."),
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED,
                                                    size=14, color=COLORS["accent"]),
                                            ft.Container(width=6),
                                            ft.Text(
                                                "llmsays auto-selects the fastest available provider",
                                                size=12, color=COLORS["accent"],
                                            ),
                                        ]
                                    ),
                                    bgcolor=COLORS["accent_soft"],
                                    border_radius=8,
                                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                    margin=ft.margin.symmetric(vertical=8),
                                ),
                                _divider(),
                                ft.Container(height=8),
                                *[ft.Container(content=row, margin=ft.margin.only(bottom=12))
                                  for row in provider_rows],
                                error_text,
                                info_text,
                                ft.Container(height=16),
                                _accent_btn("Save & Start Chatting →", save_and_continue, width=400),
                            ],
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        padding=ft.padding.symmetric(horizontal=32, vertical=28),
                        width=500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            alignment=ft.alignment.center,
            bgcolor=COLORS["bg_deep"],
        )

    # ─────────────────────────────────────────────────────────────────────────
    # CHAT PAGE
    # ─────────────────────────────────────────────────────────────────────────
    def chat_page(self):
        from llm.llm_service import LLMService
        from voice.stt import STTEngine
        from voice.tts import TTSEngine
        from voice.wake_word import WakeWordDetector
        from tools.tool_router import execute as tool_execute

        llm = LLMService(api_keys=self.state.api_keys)
        stt = STTEngine()
        tts = TTSEngine()

        # ── State refs ────────────────────────────────────────────────────────
        messages_col = ft.ListView(spacing=2, auto_scroll=True, expand=True)
        input_ref    = ft.Ref[ft.TextField]()
        status_ref   = ft.Ref[ft.Text]()
        dot_ref      = ft.Ref[ft.Container]()
        mic_ref      = ft.Ref[ft.IconButton]()
        waveform     = WaveformWidget(n_bars=9, color=COLORS["mic_active"])
        waveform_box = ft.Container(
            content=waveform.control,
            height=50,
            visible=False,
            alignment=ft.alignment.center,
        )
        wake_indicator = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(ft.Icons.WIFI_TETHERING_ROUNDED,
                                        color=COLORS["success"], size=16),
                    ),
                    ft.Container(width=6),
                    ft.Text(f'Listening for "{WAKE_WORD.title()}"…', size=12,
                            color=COLORS["success"]),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            visible=False,
            bgcolor=ft.Colors.with_opacity(0.1, COLORS["success"]),
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=14, vertical=6),
        )

        # ── Status helpers ────────────────────────────────────────────────────
        STATUS_LABELS = {
            AssistantStatus.IDLE:      ("● Idle",     COLORS["text_muted"],   "#3A4050"),
            AssistantStatus.WAKE:      ("◉ Awake",    COLORS["success"],      "#1A3A20"),
            AssistantStatus.LISTENING: ("🎙 Listening", COLORS["mic_active"], "#3A1A1A"),
            AssistantStatus.THINKING:  ("⏳ Thinking", COLORS["accent"],      "#1A2A3A"),
            AssistantStatus.SPEAKING:  ("🔊 Speaking", "#A855F7",             "#2A1A3A"),
            AssistantStatus.ERROR:     ("⚠ Error",    COLORS["error"],        "#3A1A1A"),
        }

        def update_status(s: AssistantStatus):
            label, color, bg = STATUS_LABELS.get(s, ("●", COLORS["text_muted"], "#3A4050"))
            if status_ref.current:
                status_ref.current.value = label
                status_ref.current.color = color
            if dot_ref.current:
                dot_ref.current.bgcolor = bg
            waveform_box.visible = s in (AssistantStatus.LISTENING, AssistantStatus.SPEAKING)
            waveform.animate(self.page, waveform_box.visible)
            self.page.update()

        # ── Message rendering ─────────────────────────────────────────────────
        def add_message_ui(msg: ChatMessage):
            messages_col.controls.append(_chat_bubble(msg))
            self.page.update()

        self.state.on_status_change = update_status
        self.state.on_new_message   = add_message_ui

        # Render existing history
        for msg in self.state.chat_history:
            messages_col.controls.append(_chat_bubble(msg))

        # ── Core pipeline ─────────────────────────────────────────────────────
        def process_query(user_text: str):
            if not user_text.strip():
                return
            self.state.add_message("user", user_text)
            self.state.set_status(AssistantStatus.THINKING)

            result = llm.chat(user_text)
            intent     = result.get("intent", "general_chat")
            parameters = result.get("parameters", {})
            response   = result.get("response", "")

            # Execute tool if needed
            tool_msg = tool_execute(intent, parameters)
            if tool_msg:
                response = tool_msg + " " + response

            self.state.add_message("assistant", response)
            self.state.set_status(AssistantStatus.SPEAKING)

            def on_speech_done():
                self.state.set_status(AssistantStatus.IDLE)
                if wake_detector.is_running:
                    wake_detector.resume()

            wake_detector.pause()
            tts.speak(response, on_done=on_speech_done)

        # ── Send from text input ──────────────────────────────────────────────
        def send_text(e):
            txt = (input_ref.current.value or "").strip()
            if not txt:
                return
            input_ref.current.value = ""
            self.page.update()
            threading.Thread(target=process_query, args=(txt,), daemon=True).start()

        # ── Mic button (push-to-talk) ─────────────────────────────────────────
        mic_listening = [False]

        def toggle_mic(e):
            if mic_listening[0]:
                return
            mic_listening[0] = True
            mic_ref.current.icon = ft.Icons.STOP_CIRCLE_ROUNDED
            mic_ref.current.icon_color = COLORS["mic_active"]
            self.state.set_status(AssistantStatus.LISTENING)
            self.page.update()

            def listen_thread():
                text = stt.listen_once(timeout=8, phrase_limit=12)
                mic_listening[0] = False
                mic_ref.current.icon = ft.Icons.MIC_ROUNDED
                mic_ref.current.icon_color = COLORS["mic_idle"]
                if text:
                    process_query(text)
                else:
                    self.state.set_status(AssistantStatus.IDLE)
                    self.page.update()

            threading.Thread(target=listen_thread, daemon=True).start()

        # ── Wake word detection ───────────────────────────────────────────────
        def on_wake():
            self.state.set_status(AssistantStatus.LISTENING)
            self.page.update()
            text = stt.listen_once(timeout=8, phrase_limit=12)
            if text:
                process_query(text)
            else:
                self.state.set_status(AssistantStatus.IDLE)
                self.page.update()

        wake_detector = WakeWordDetector(stt, on_wake=on_wake)

        def toggle_wake(e):
            toggle_btn = wake_toggle_ref.current
            if wake_detector.is_running:
                wake_detector.stop()
                toggle_btn.icon = ft.Icons.WIFI_OFF_ROUNDED
                toggle_btn.tooltip = "Start wake-word listener"
                toggle_btn.icon_color = COLORS["text_muted"]
                wake_indicator.visible = False
            else:
                wake_detector.start()
                toggle_btn.icon = ft.Icons.WIFI_TETHERING_ROUNDED
                toggle_btn.tooltip = 'Stop wake-word listener'
                toggle_btn.icon_color = COLORS["success"]
                wake_indicator.visible = True
            self.page.update()

        wake_toggle_ref = ft.Ref[ft.IconButton]()

        # ── Settings / logout ─────────────────────────────────────────────────
        def open_settings(e):
            self.navigate("api_setup")

        def do_logout(e):
            wake_detector.stop()
            tts.stop()
            self.state.logout()
            self.navigate("login")

        # ── Top bar ───────────────────────────────────────────────────────────
        display_name = (self.state.current_user or {}).get("display_name", "User")
        top_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.GRAPHIC_EQ_ROUNDED,
                                                color="#FFFFFF", size=20),
                                width=40,
                                height=40,
                                border_radius=12,
                                gradient=ft.LinearGradient(
                                    begin=ft.alignment.top_left,
                                    end=ft.alignment.bottom_right,
                                    colors=[COLORS["accent"], "#7C3AED"],
                                ),
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(width=10),
                            ft.Column(
                                [
                                    ft.Text(APP_NAME, size=16, weight=ft.FontWeight.BOLD,
                                            color=COLORS["text_primary"]),
                                    ft.Text(f"Hello, {display_name}",
                                            size=11, color=COLORS["text_muted"]),
                                ],
                                spacing=1,
                                tight=True,
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                ref=dot_ref,
                                width=80,
                                height=28,
                                border_radius=14,
                                bgcolor="#3A4050",
                                alignment=ft.alignment.center,
                                content=ft.Text(ref=status_ref, value="● Idle",
                                                size=11, color=COLORS["text_muted"]),
                            ),
                            ft.Container(width=8),
                            ft.IconButton(
                                ref=wake_toggle_ref,
                                icon=ft.Icons.WIFI_OFF_ROUNDED,
                                icon_color=COLORS["text_muted"],
                                tooltip="Start wake-word listener",
                                on_click=toggle_wake,
                                icon_size=20,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.TUNE_ROUNDED,
                                icon_color=COLORS["text_secondary"],
                                tooltip="API Settings",
                                on_click=open_settings,
                                icon_size=20,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.LOGOUT_ROUNDED,
                                icon_color=COLORS["text_secondary"],
                                tooltip="Sign out",
                                on_click=do_logout,
                                icon_size=20,
                            ),
                        ]
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            bgcolor=COLORS["bg_card"],
            border=ft.border.only(bottom=ft.BorderSide(1, COLORS["border"])),
        )

        # ── Bottom input bar ──────────────────────────────────────────────────
        input_bar = ft.Container(
            content=ft.Column(
                [
                    wake_indicator,
                    waveform_box,
                    ft.Row(
                        [
                            ft.IconButton(
                                ref=mic_ref,
                                icon=ft.Icons.MIC_ROUNDED,
                                icon_color=COLORS["mic_idle"],
                                tooltip="Hold to speak",
                                on_click=toggle_mic,
                                style=ft.ButtonStyle(
                                    bgcolor={"": COLORS["bg_elevated"], "hovered": COLORS["accent_soft"]},
                                    shape=ft.CircleBorder(),
                                    padding=12,
                                ),
                            ),
                            ft.TextField(
                                ref=input_ref,
                                hint_text=f'Ask Dogesh anything… or say "{WAKE_WORD.title()}"',
                                border_color=COLORS["border"],
                                focused_border_color=COLORS["accent"],
                                bgcolor=COLORS["bg_elevated"],
                                hint_style=ft.TextStyle(color=COLORS["text_muted"], size=13),
                                text_style=ft.TextStyle(color=COLORS["text_primary"], size=14),
                                border_radius=24,
                                content_padding=ft.padding.symmetric(horizontal=20, vertical=12),
                                on_submit=send_text,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SEND_ROUNDED,
                                icon_color=COLORS["accent"],
                                tooltip="Send",
                                on_click=send_text,
                                style=ft.ButtonStyle(
                                    bgcolor={"": COLORS["accent_soft"], "hovered": COLORS["accent"]},
                                    shape=ft.CircleBorder(),
                                    padding=12,
                                ),
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=COLORS["bg_card"],
            border=ft.border.only(top=ft.BorderSide(1, COLORS["border"])),
        )

        # ── Welcome message ───────────────────────────────────────────────────
        if not self.state.chat_history:
            welcome = ChatMessage(
                role="assistant",
                content=f"Hi {display_name}! 👋 I'm Dogesh, your personal assistant. "
                        f'Say "{WAKE_WORD.title()}" or type your question below. '
                        f"I can search the web, answer questions, and more!",
                timestamp=__import__("datetime").datetime.now().strftime("%H:%M"),
            )
            self.state.chat_history.append(welcome)
            messages_col.controls.append(_chat_bubble(welcome))

        return ft.Column(
            [
                top_bar,
                ft.Container(
                    content=messages_col,
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    bgcolor=COLORS["bg_deep"],
                ),
                input_bar,
            ],
            expand=True,
            spacing=0,
        )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

def main_app(page: ft.Page):
    """Entry point called by flet.app(target=main_app)."""

    # ── Page config ───────────────────────────────────────────────────────────
    page.title        = APP_NAME
    page.theme_mode   = ft.ThemeMode.DARK
    page.bgcolor      = COLORS["bg_deep"]
    page.padding      = 0
    page.spacing      = 0
    page.window.width  = 980
    page.window.height = 720
    page.window.min_width  = 720
    page.window.min_height = 560
    page.fonts = {
        "mono": "https://fonts.gstatic.com/s/robotomono/v23/L0x5DF4xlVMF-BfR8bXMIhJHg45mwgGEFl0_3vqPQ.woff2",
    }
    page.theme = ft.Theme(
        color_scheme_seed=COLORS["accent"],
        visual_density=ft.ThemeVisualDensity.COMPACT,
    )

    state = AppState()
    db    = Database()

    # ── Router ────────────────────────────────────────────────────────────────
    current_route = ["login"]

    def navigate(route: str):
        current_route[0] = route
        page.controls.clear()
        builder = PageBuilder(page, state, db, navigate)
        route_map = {
            "login":      builder.login_page,
            "register":   builder.register_page,
            "calibration":builder.calibration_page,
            "api_setup":  builder.api_setup_page,
            "chat":       builder.chat_page,
        }
        fn = route_map.get(route, builder.login_page)
        page.controls.append(fn())
        page.update()

    # ── Start ─────────────────────────────────────────────────────────────────
    navigate("login")
