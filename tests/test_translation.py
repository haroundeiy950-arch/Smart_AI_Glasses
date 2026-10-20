import tempfile,unittest
from pathlib import Path
from database import DatabaseManager
from translator_service import TranslatorService

class TranslationTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.db=DatabaseManager('sqlite',Path(self.tmp.name)/'test.db'); self.service=TranslatorService(self.db)
    def tearDown(self): self.tmp.cleanup()
    def test_kinyarwanda_offline(self):
        r=self.service.translate('hello','en','rw'); self.assertEqual(r.translated_text,'Muraho'); self.assertEqual(r.provider,'offline-phrasebook')
    def test_arabic_kinyarwanda(self): self.assertEqual(self.service.translate('شكرا','ar','rw').translated_text,'Murakoze')
