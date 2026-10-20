import tempfile,unittest
from pathlib import Path
from database import DatabaseManager
from privacy_manager import PrivacyManager

class PrivacyTests(unittest.TestCase):
    def test_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            db=DatabaseManager('sqlite',Path(d)/'test.db'); p=PrivacyManager(db); p.set_permission('microphone',True); self.assertTrue(p.get_permissions()['microphone'])
            p.set_permission('microphone',False)
            with self.assertRaises(PermissionError): p.require('microphone')
