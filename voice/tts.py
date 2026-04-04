"""
Dogesh Assistant – Text-to-Speech
Uses pyttsx3 (offline, cross-platform).
"""

import threading
from config import TTS_RATE

try:
    import pyttsx3 as _pyttsx3
    _TTS_OK = True
except Exception:
    _TTS_OK = False


class TTSEngine:
    """Thread-safe TTS wrapper. Speak requests are queued & handled on a worker thread."""

    def __init__(self):
        self._engine = None
        self._lock   = threading.Lock()
        self._busy   = False
        if _TTS_OK:
            self._init_engine()

    def _init_engine(self):
        try:
            self._engine = _pyttsx3.init()
            self._engine.setProperty("rate",   TTS_RATE)
            self._engine.setProperty("volume", 1.0)
            # Prefer a female voice if available
            voices = self._engine.getProperty("voices")
            for v in voices:
                if "female" in (v.name or "").lower() or "zira" in (v.id or "").lower():
                    self._engine.setProperty("voice", v.id)
                    break
        except Exception as e:
            print(f"[TTS] Init warning: {e}")
            self._engine = None

    # ── Public ────────────────────────────────────────────────────────────────

    def speak(self, text: str, on_done: callable = None):
        """
        Speak *text* on a background thread.
        on_done() is called once speech finishes.
        """
        if not text:
            if on_done:
                on_done()
            return
        t = threading.Thread(target=self._speak_sync, args=(text, on_done), daemon=True)
        t.start()

    def stop(self):
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass

    @property
    def available(self):
        return self._engine is not None

    # ── Private ───────────────────────────────────────────────────────────────

    def _speak_sync(self, text: str, on_done):
        with self._lock:
            self._busy = True
            if self._engine:
                try:
                    self._engine.say(text)
                    self._engine.runAndWait()
                except Exception as e:
                    print(f"[TTS] Speak error: {e}")
            self._busy = False
        if on_done:
            try:
                on_done()
            except Exception:
                pass
