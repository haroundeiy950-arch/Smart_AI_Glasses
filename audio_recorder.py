"""Optional microphone WAV recording used by meeting assistant."""
from __future__ import annotations
import threading,wave
from datetime import datetime
from pathlib import Path
from config import RECORDED_SOUNDS_DIR
from privacy_manager import PrivacyManager

class AudioRecorder:
    def __init__(self,privacy: PrivacyManager): self.privacy=privacy; self._stream=None; self._audio=None; self._frames=[]; self._thread=None; self._running=False; self.output_path: Path|None=None
    @property
    def available(self)->bool:
        try: import pyaudio; return True
        except ImportError: return False
    def start(self,channels: int=1,rate: int=16000,chunk: int=1024,device_index: int|None=None)->Path:
        self.privacy.require("microphone"); self.privacy.require("meeting_recording")
        if self._running: raise RuntimeError("Recording is already active")
        try: import pyaudio
        except ImportError as exc: raise RuntimeError("Install PyAudio for direct meeting recording. Typed transcripts still work without it") from exc
        RECORDED_SOUNDS_DIR.mkdir(parents=True,exist_ok=True); self.output_path=RECORDED_SOUNDS_DIR/f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        self._audio=pyaudio.PyAudio(); self._stream=self._audio.open(format=pyaudio.paInt16,channels=channels,rate=rate,input=True,input_device_index=device_index,frames_per_buffer=chunk); self._frames=[]; self._running=True
        def worker():
            while self._running:
                try: self._frames.append(self._stream.read(chunk,exception_on_overflow=False))
                except Exception: break
        self._thread=threading.Thread(target=worker,daemon=True); self._thread.start(); self._meta=(channels,rate,pyaudio.paInt16); return self.output_path
    def stop(self)->Path:
        if not self._running or not self._stream or not self._audio or not self.output_path: raise RuntimeError("No active recording")
        self._running=False
        if self._thread: self._thread.join(timeout=2)
        self._stream.stop_stream(); self._stream.close(); sample_width=self._audio.get_sample_size(self._meta[2]); self._audio.terminate()
        with wave.open(str(self.output_path),'wb') as wf:
            wf.setnchannels(self._meta[0]); wf.setsampwidth(sample_width); wf.setframerate(self._meta[1]); wf.writeframes(b''.join(self._frames))
        path=self.output_path; self._stream=self._audio=None; return path
    @property
    def recording(self)->bool: return self._running
