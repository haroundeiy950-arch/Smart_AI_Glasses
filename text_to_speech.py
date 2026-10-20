"""Offline text-to-speech through pyttsx3."""
from __future__ import annotations
import threading
from pathlib import Path
from typing import Any
from config import OUTPUT_VOICE_DIR

class TextToSpeech:
    def __init__(self): self._lock=threading.Lock(); self._engine_instance: Any|None=None
    @property
    def available(self)->bool:
        try: import pyttsx3; return True
        except ImportError: return False
    def _engine(self):
        if self._engine_instance is None:
            try: import pyttsx3
            except ImportError as exc: raise RuntimeError("Install pyttsx3") from exc
            self._engine_instance=pyttsx3.init(); self._engine_instance.setProperty("rate",170)
        return self._engine_instance
    def speak(self,text: str)->None:
        if not text.strip(): return
        with self._lock:
            e=self._engine(); e.say(text); e.runAndWait()
    def save_to_file(self,text: str,filename: str="voice_output.mp3")->Path:
        OUTPUT_VOICE_DIR.mkdir(parents=True,exist_ok=True); path=OUTPUT_VOICE_DIR/filename
        with self._lock:
            e=self._engine(); e.save_to_file(text,str(path)); e.runAndWait()
        return path
