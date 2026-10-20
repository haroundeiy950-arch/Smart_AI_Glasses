import tempfile,unittest
from pathlib import Path
from database import DatabaseManager

class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=DatabaseManager('sqlite',Path(self.tmp.name)/'test.db')
    def tearDown(self): self.tmp.cleanup()
    def test_schema_and_counts(self):
        counts=self.db.dashboard_counts(); self.assertIn('known_people',counts); self.assertEqual(counts['meetings'],0)
    def test_person_translation_reminder(self):
        pid=self.db.upsert_known_person('p1','Person One','','','',str(Path(self.tmp.name)/'p1'),True)
        self.assertEqual(self.db.get_known_person(pid)['name'],'Person One')
        self.db.add_translation('hello','Muraho','en','rw','offline',None)
        self.assertEqual(len(self.db.list_translations()),1)
