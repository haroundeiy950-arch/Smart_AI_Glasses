"""The single control system that creates, connects, monitors and shuts down all modules."""
from __future__ import annotations
import importlib.util,platform,sys
from typing import Any
from ai_service import AIService
from assistant_core import AssistantCore
from audio_recorder import AudioRecorder
from backup_manager import BackupManager
from camera_service import CameraService
from config import PROJECT_NAME,PROJECT_VERSION,ensure_project_folders
from database import DatabaseManager
from data_control import DataControlService
from device_manager import DeviceManager
from emotion_analyzer import EmotionAnalyzer
from face_identifier import FaceIdentifier
from logger import configure_logging,get_logger
from meeting_assistant import MeetingAssistant
from notification_service import NotificationService
from object_detector import ObjectDetector
from ocr_reader import OCRReader
from privacy_manager import PrivacyManager
from reminder_service import ReminderService
from security import DataProtector,SecurityManager
from speech_to_text import SpeechToText
from text_to_speech import TextToSpeech
from translator_service import TranslatorService

configure_logging(); log=get_logger(__name__)

class SystemController:
    def __init__(self,database: DatabaseManager|None=None):
        ensure_project_folders(); self.database=database or DatabaseManager(); self.security=SecurityManager(self.database); self.security.bootstrap_admin(); self.privacy=PrivacyManager(self.database)
        self.camera=CameraService(self.privacy); self.speech_to_text=SpeechToText(self.privacy); self.text_to_speech=TextToSpeech(); self.audio_recorder=AudioRecorder(self.privacy)
        self.translator=TranslatorService(self.database); self.data_protector=DataProtector(); self.ai_service=AIService(self.database,self.privacy)
        self.face_identifier=FaceIdentifier(self.camera,self.database,self.privacy,self.security); self.object_detector=ObjectDetector(self.camera,self.privacy); self.ocr=OCRReader(self.camera,self.privacy); self.emotion=EmotionAnalyzer(self.camera,self.privacy)
        self.reminders=ReminderService(self.database); self.notifications=NotificationService(self.database,self.privacy); self.meetings=MeetingAssistant(self.database,self.translator,self.ai_service,self.privacy,self.speech_to_text,self.audio_recorder)
        self.backups=BackupManager(self.data_protector); self.devices=DeviceManager(self.database,self.camera,self.speech_to_text,self.text_to_speech); self.data_control=DataControlService(self.database)
        self.assistant=AssistantCore(self.translator,self.ai_service,self.reminders,self.database,self); self.current_user: dict[str,Any]|None=None
        log.info("%s %s initialized",PROJECT_NAME,PROJECT_VERSION)
    @property
    def user_id(self)->int|None: return int(self.current_user['id']) if self.current_user else None
    def login(self,username: str,password: str):
        result=self.security.authenticate(username,password)
        if result.success and result.user: self.current_user=result.user; self.privacy.set_user(int(result.user['id'])); self.notifications.notify("Login","Successful login","security",self.user_id); self.data_control.sync_users_json()
        return result
    def face_login(self,username: str):
        user=self.database.get_user_by_username(username.strip().lower())
        if not user: return self.security.authenticate("__missing__","")
        self.privacy.set_user(int(user['id']))
        matched=self.face_identifier.verify_user_face(int(user['id']))
        result=self.security.authenticate_face(int(user['id']),matched)
        if result.success and result.user: self.current_user=result.user; self.notifications.notify("Face Unlock","Face login successful","security",self.user_id)
        elif not result.success: self.privacy.set_user(None)
        return result
    def logout(self):
        if self.current_user: self.security.audit("LOGOUT","User logged out",user_id=self.user_id)
        self.current_user=None; self.privacy.set_user(None); self.camera.close()
    @staticmethod
    def _module(name: str,hint: str):
        found=importlib.util.find_spec(name) is not None; return {"status":"READY" if found else "OPTIONAL/MISSING","message":f"{name} installed" if found else hint}
    def health_check(self,quick: bool=False):
        health={"application":{"status":"READY","message":f"{PROJECT_NAME} {PROJECT_VERSION}"},"python":{"status":"READY","message":sys.version.split()[0]},"platform":{"status":"READY","message":platform.platform()},"database":{"status":"READY","message":self.database.engine},"opencv":self._module("cv2","Install opencv-contrib-python"),"translation":self._module("deep_translator","Install deep-translator"),"speech":self._module("speech_recognition","Install SpeechRecognition"),"tts":self._module("pyttsx3","Install pyttsx3"),"ocr":self._module("pytesseract","Install pytesseract and Tesseract desktop"),"yolo":self._module("ultralytics","Install requirements-ai.txt"),"emotion":self._module("deepface","Install requirements-ai.txt"),"audio_recording":self._module("pyaudio","Install PyAudio if direct recording is needed"),"cloud_ai":self._module("openai","Install openai and set OPENAI_API_KEY"),"encryption":{"status":"READY" if self.data_protector.available else "OPTIONAL/MISSING","message":"Fernet available" if self.data_protector.available else "Install cryptography"}}
        health['camera']={"status":"NOT CHECKED","message":"Run full health check"}
        if not quick and health['opencv']['status']=="READY":
            status=self.camera.status(); health['camera']={"status":"READY" if status.available else "ERROR","message":status.message}
        return health
    def dashboard(self): return {"counts":self.database.dashboard_counts(),"health":self.health_check(True),"notifications":self.notifications.list(self.user_id,True) if self.current_user else []}
    def ai_context(self):
        h=self.health_check(True); ready=sum(1 for x in h.values() if x['status']=='READY')
        return {"health_summary":f"{ready}/{len(h)} components ready","database_engine":self.database.engine,"known_people":len(self.database.list_known_people()),"meetings":len(self.database.list_meetings()),"privacy":self.privacy.get_permissions(),"current_user":(self.current_user or {}).get('username')}
    def shutdown(self):
        if self.audio_recorder.recording:
            try: self.audio_recorder.stop()
            except Exception: pass
        self.camera.close(); log.info("System shut down")
