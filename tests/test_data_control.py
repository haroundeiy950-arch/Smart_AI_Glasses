import tempfile,unittest
from pathlib import Path
from data_control import DataControlService
from database import DatabaseManager
from security import SecurityManager

class DataControlTests(unittest.TestCase):
    def test_users_json_and_export(self):
        with tempfile.TemporaryDirectory() as d:
            db=DatabaseManager('sqlite',Path(d)/'test.db'); sec=SecurityManager(db); sec.bootstrap_admin(); service=DataControlService(db)
            path=service.sync_users_json(); self.assertTrue(path.exists()); self.assertNotIn('password_hash',path.read_text(encoding='utf-8'))
            export=service.export_table_csv('users'); self.assertTrue(export.exists())
