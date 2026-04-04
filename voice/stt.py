"""
Dogesh Assistant – Speech-to-Text
Wraps SpeechRecognition with Google STT (internet) or Sphinx (offline fallback).
"""

import threading
import time
from typing import Optional, Callable
from config import STT_TIMEOUT, STT_PHRASE_LIMIT

try:
    import speech_recognition as sr
    _SR_OK = True
except ImportError:
    _SR_OK = False


class STTEngine:
    """
    Provides:
      • listen_once()  – blocking, returns transcript string
      • calibrate()    – measures ambient noise, returns energy_threshold
    """

    def __init__(self):
        self._r   = sr.Recognizer() if _SR_OK else None
        self._mic = None
        self._mic_lock = threading.Lock()
        self.available = _SR_OK

    # ── Microphone ────────────────────────────────────────────────────────────

    def _get_mic(self):
        if self._mic is None:
            self._mic = sr.Microphone()
        return self._mic

    # ── Calibration ───────────────────────────────────────────────────────────

    def calibrate(self, duration: float = 2.0, on_progress: Callable = None) -> float:
        """
        Sample ambient noise and tune energy_threshold.
        Returns the calibrated threshold.
        """
        if not self._r:
            return 300.0
        try:
            if on_progress:
                on_progress("Sampling ambient noise…")
            with self._get_mic() as src:
                self._r.adjust_for_ambient_noise(src, duration=duration)
            if on_progress:
                on_progress(f"Calibrated (threshold={self._r.energy_threshold:.0f})")
            return self._r.energy_threshold
        except Exception as e:
            if on_progress:
                on_progress(f"Calibration error: {e}")
            return 300.0

    def set_threshold(self, threshold: float):
        if self._r:
            self._r.energy_threshold = threshold
            self._r.dynamic_energy_threshold = False   # lock to calibrated value

    # ── Listen ────────────────────────────────────────────────────────────────

    def listen_once(
        self,
        timeout: float = STT_TIMEOUT,
        phrase_limit: float = STT_PHRASE_LIMIT,
        on_listening: Callable = None,
    ) -> Optional[str]:
        """
        Block until a phrase is detected, then return transcript (or None).
        """
        if not self._r:
            return None
        try:
            if on_listening:
                on_listening("Listening…")
            with self._get_mic() as src:
                audio = self._r.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
            if on_listening:
                on_listening("Recognising…")
            text = self._r.recognize_google(audio)
            return text.strip()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"[STT] Error: {e}")
            return None

    # ── Wake word helper ──────────────────────────────────────────────────────

    def listen_for_wake(
        self,
        wake_phrase: str = "hey dogesh",
        timeout: float = 3.0,
        phrase_limit: float = 5.0,
    ) -> bool:
        """
        Listen for a short chunk and check if it contains the wake phrase.
        Returns True if wake word detected.
        """
        if not self._r:
            return False
        try:
            with self._get_mic() as src:
                audio = self._r.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
            text = self._r.recognize_google(audio).lower()
            return wake_phrase.lower() in text
        except Exception:
            return False
