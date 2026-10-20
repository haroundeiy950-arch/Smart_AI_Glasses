import tempfile,unittest
from pathlib import Path
from database import DatabaseManager
from security import PasswordManager,SecurityManager

class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=DatabaseManager('sqlite',Path(self.tmp.name)/'test.db'); self.sec=SecurityManager(self.db); self.sec.bootstrap_admin()
    def tearDown(self): self.tmp.cleanup()
    def test_password_hash(self):
        h,s=PasswordManager.hash_password('Strong@123'); self.assertTrue(PasswordManager.verify_password('Strong@123',h,s)); self.assertFalse(PasswordManager.verify_password('wrong',h,s))
    def test_login(self):
        self.assertTrue(self.sec.authenticate('admin','Admin@12345').success); self.assertFalse(self.sec.authenticate('admin','bad').success)
    def test_create_user(self):
        uid=self.sec.create_user('haroun','Strong@123','Haroun','user','rw'); self.assertEqual(self.db.get_user(uid)['preferred_language'],'rw')
