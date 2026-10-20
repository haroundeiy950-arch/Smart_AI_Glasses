"""Speech-to-text from microphone or audio file."""
from __future__ import annotations
from pathlib import Path
from privacy_manager import PrivacyManager

class SpeechToText:
    def __init__(self,privacy: PrivacyManager): self.privacy=privacy
    @staticmethod
    def _sr():
        try: import speech_recognition as sr; return sr
        except ImportError as exc: raise RuntimeError("Install SpeechRecognition") from exc
    def list_microphones(self)->list[str]:
        try:
            sr=self._sr()
            return sr.Microphone.list_microphone_names()
        except Exception:
            return []
    def listen_once(self,language: str="en-US",timeout: float=8,phrase_time_limit: float=20,microphone_index: int|None=None)->str:
        self.privacy.require("microphone"); sr=self._sr(); recognizer=sr.Recognizer()
        try:
            with sr.Microphone(device_index=microphone_index) as source:
                recognizer.adjust_for_ambient_noise(source,duration=0.5); audio=recognizer.listen(source,timeout=timeout,phrase_time_limit=phrase_time_limit)
            return recognizer.recognize_google(audio,language=language)
        except sr.WaitTimeoutError: raise RuntimeError("No speech detected before timeout")
        except sr.UnknownValueError: raise RuntimeError("Speech was not clear enough to understand")
        except sr.RequestError as exc: raise RuntimeError(f"Online speech service error: {exc}") from exc
        except OSError as exc: raise RuntimeError(f"Microphone unavailable: {exc}") from exc
    def transcribe_wav(self,path: str|Path,language: str="en-US")->str:
        sr=self._sr(); recognizer=sr.Recognizer()
        with sr.AudioFile(str(path)) as source: audio=recognizer.record(source)
        try: return recognizer.recognize_google(audio,language=language)
        except sr.UnknownValueError: raise RuntimeError("Audio could not be understood")
        except sr.RequestError as exc: raise RuntimeError(f"Speech service error: {exc}") from exc
