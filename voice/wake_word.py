"""
Dogesh Assistant – Wake Word Detector
Runs as a background daemon thread; fires a callback when "Hey Dogesh" is heard.
"""

import threading
from typing import Callable, Optional
from config import WAKE_WORD, WAKE_DETECT_INTERVAL
from voice.stt import STTEngine


class WakeWordDetector:
    """
    Daemon thread that continuously listens for WAKE_WORD.
    Once detected, calls on_wake() on the calling thread (via callback).
    """

    def __init__(self, stt: STTEngine, on_wake: Callable, on_error: Callable = None):
        self._stt      = stt
        self._on_wake  = on_wake
        self._on_error = on_error
        self._running  = False
        self._thread: Optional[threading.Thread] = None
        self._paused   = False      # pause during active command listening / speaking

    # ── Control ───────────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="WakeWordThread")
        self._thread.start()

    def stop(self):
        self._running = False

    def pause(self):
        """Temporarily stop processing (e.g. while assistant is speaking)."""
        self._paused = True

    def resume(self):
        self._paused = False

    @property
    def is_running(self):
        return self._running and (self._thread is not None) and self._thread.is_alive()

    # ── Loop ──────────────────────────────────────────────────────────────────

    def _loop(self):
        import time
        while self._running:
            if self._paused:
                time.sleep(0.3)
                continue
            try:
                detected = self._stt.listen_for_wake(
                    wake_phrase=WAKE_WORD,
                    timeout=WAKE_DETECT_INTERVAL,
                    phrase_limit=5.0,
                )
                if detected and not self._paused:
                    self._on_wake()
            except Exception as e:
                if self._on_error:
                    self._on_error(str(e))
