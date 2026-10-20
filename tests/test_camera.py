import tempfile,unittest
from pathlib import Path
from camera_service import CameraService,CameraStatus
from database import DatabaseManager
from privacy_manager import PrivacyManager

class CameraTests(unittest.TestCase):
    def test_status_type_without_requiring_camera(self):
        with tempfile.TemporaryDirectory() as d:
            db=DatabaseManager('sqlite',Path(d)/'test.db'); privacy=PrivacyManager(db); privacy.set_permission('camera',False); cam=CameraService(privacy); status=cam.status(); self.assertIsInstance(status,CameraStatus); self.assertFalse(status.available)
