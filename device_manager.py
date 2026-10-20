"""Probe camera, microphones, speakers and basic platform information."""
from __future__ import annotations
import platform
from typing import Any
from camera_service import CameraService
from database import DatabaseManager
from speech_to_text import SpeechToText
from text_to_speech import TextToSpeech

class DeviceManager:
    def __init__(self,database: DatabaseManager,camera: CameraService,speech: SpeechToText,tts: TextToSpeech): self.db=database; self.camera=camera; self.speech=speech; self.tts=tts
    def scan(self)->dict[str,Any]:
        camera=self.camera.status(); microphones=self.speech.list_microphones(); result={"platform":platform.platform(),"camera":{"available":camera.available,"index":camera.index,"message":camera.message},"microphones":microphones,"text_to_speech":self.tts.available}
        self.db.add_device_event("system",platform.node() or "computer","scanned",str(result)); return result
