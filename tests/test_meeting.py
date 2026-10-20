import tempfile,unittest
from pathlib import Path
from ai_service import AIService
from audio_recorder import AudioRecorder
from database import DatabaseManager
from meeting_assistant import MeetingAssistant
from privacy_manager import PrivacyManager
from speech_to_text import SpeechToText
from translator_service import TranslatorService

class MeetingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=DatabaseManager('sqlite',Path(self.tmp.name)/'test.db'); self.privacy=PrivacyManager(self.db); self.privacy.set_user(None); self.privacy.set_permission('meeting_recording',True)
        self.tr=TranslatorService(self.db); self.ai=AIService(self.db,self.privacy); self.service=MeetingAssistant(self.db,self.tr,self.ai,self.privacy,SpeechToText(self.privacy),AudioRecorder(self.privacy))
    def tearDown(self): self.tmp.cleanup()
    def test_save_and_extract(self):
        text='We agreed to launch Friday. Task: Alice must prepare the report.'
        r=self.service.save_meeting('Planning',['Alice'],text,'en','en',True,False,None,translate_transcript=False)
        self.assertEqual(r.meeting_id,1); self.assertTrue(r.tasks); self.assertTrue(r.decisions)
