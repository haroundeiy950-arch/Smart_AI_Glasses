import tempfile,unittest
from pathlib import Path
from database import DatabaseManager
from privacy_manager import PrivacyManager
from speech_to_text import SpeechToText
from text_to_speech import TextToSpeech

class SpeechTests(unittest.TestCase):
    def test_services_construct(self):
        with tempfile.TemporaryDirectory() as d:
            db=DatabaseManager('sqlite',Path(d)/'test.db'); privacy=PrivacyManager(db)
            self.assertIsInstance(SpeechToText(privacy).list_microphones(),list); self.assertIsInstance(TextToSpeech().available,bool)
