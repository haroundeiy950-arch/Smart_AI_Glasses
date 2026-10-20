import tempfile,unittest
from pathlib import Path
from ai_service import AIService
from database import DatabaseManager
from privacy_manager import PrivacyManager

class AITests(unittest.TestCase):
    def test_offline_unknown_person_rule(self):
        with tempfile.TemporaryDirectory() as d:
            db=DatabaseManager('sqlite',Path(d)/'test.db'); privacy=PrivacyManager(db); service=AIService(db,privacy)
            result=service.ask('هذا الشخص غير معروف')
            self.assertIn('غير مسجل',result.answer); self.assertEqual(result.provider,'offline-rules')
