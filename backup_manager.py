"""Create, list and restore project-data backups. Encrypted backups are optional."""
from __future__ import annotations
import json,shutil,tempfile,zipfile
from datetime import datetime
from pathlib import Path
from config import BACKUPS_DIR,DATA_DIR,EXPORTS_DIR,IMAGES_DIR,LOGS_DIR,SOUNDS_DIR,SQLITE_PATH
from security import DataProtector

class BackupManager:
    def __init__(self,protector: DataProtector): self.protector=protector
    def create_backup(self,include_media: bool=False,encrypted: bool=False)->Path:
        BACKUPS_DIR.mkdir(parents=True,exist_ok=True); stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); zip_path=BACKUPS_DIR/f"smart_ai_glasses_backup_{stamp}.zip"
        with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
            sources=[SQLITE_PATH,DATA_DIR/'users.json',LOGS_DIR]
            if include_media: sources.extend([IMAGES_DIR,SOUNDS_DIR])
            for source in sources:
                if not source.exists(): continue
                if source.is_file(): z.write(source,source.relative_to(DATA_DIR.parent))
                else:
                    for path in source.rglob('*'):
                        if path.is_file() and BACKUPS_DIR not in path.parents: z.write(path,path.relative_to(DATA_DIR.parent))
            z.writestr('backup_manifest.json',json.dumps({"created_at":datetime.now().isoformat(),"include_media":include_media},indent=2))
        if encrypted:
            if not self.protector.available: raise RuntimeError("Install cryptography for encrypted backups")
            encrypted_path=zip_path.with_suffix('.zip.enc'); encrypted_path.write_text(self.protector.encrypt_text(zip_path.read_bytes().hex()),encoding='utf-8'); zip_path.unlink(); return encrypted_path
        return zip_path
    def list_backups(self)->list[Path]: BACKUPS_DIR.mkdir(parents=True,exist_ok=True); return sorted([p for p in BACKUPS_DIR.iterdir() if p.is_file()],reverse=True)
    def restore_backup(self,path: str|Path)->None:
        path=Path(path)
        if not path.exists(): raise FileNotFoundError(path)
        if path.suffix=='.enc':
            if not self.protector.available: raise RuntimeError("Encryption support unavailable")
            raw=bytes.fromhex(self.protector.decrypt_text(path.read_text(encoding='utf-8'))); temp=Path(tempfile.mkstemp(suffix='.zip')[1]); temp.write_bytes(raw); archive=temp
        else: archive=path
        try:
            with zipfile.ZipFile(archive,'r') as z: z.extractall(DATA_DIR.parent)
        finally:
            if archive!=path: archive.unlink(missing_ok=True)
