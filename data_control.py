"""Central data export, reporting and privacy deletion service."""
from __future__ import annotations
import csv,json
from datetime import datetime
from pathlib import Path
from typing import Any
from config import DATA_DIR,EXPORTS_DIR
from database import DatabaseManager

class DataControlService:
    SAFE_TABLES={"users","known_people","unknown_events","translations","meetings","meeting_notes","security_logs","ai_history","settings","reminders","notifications","device_events","command_history"}
    def __init__(self,database: DatabaseManager): self.db=database
    def sync_users_json(self)->Path:
        rows=self.db.list_users(); safe=[{k:v for k,v in row.items() if k not in {'password_hash','salt'}} for row in rows]; path=DATA_DIR/'users.json'; path.write_text(json.dumps(safe,ensure_ascii=False,indent=2,default=str),encoding='utf-8'); return path
    def export_table_csv(self,table: str)->Path:
        if table not in self.SAFE_TABLES: raise ValueError("Unsupported table")
        rows=self.db.list_users() if table=='users' else self.db.fetch_all(f"SELECT * FROM {table} ORDER BY id")
        EXPORTS_DIR.mkdir(parents=True,exist_ok=True); path=EXPORTS_DIR/f"{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        if not rows: path.write_text('',encoding='utf-8-sig'); return path
        with path.open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0].keys())); writer.writeheader(); writer.writerows(rows)
        return path
    def export_all_json(self)->Path:
        payload={}
        for table in sorted(self.SAFE_TABLES):
            payload[table]=self.db.list_users() if table=='users' else self.db.fetch_all(f"SELECT * FROM {table} ORDER BY id")
        EXPORTS_DIR.mkdir(parents=True,exist_ok=True); path=EXPORTS_DIR/f"all_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"; path.write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),encoding='utf-8'); self.sync_users_json(); return path
    def system_report(self,health: dict[str,Any],privacy: dict[str,Any])->Path:
        report={"generated_at":datetime.now().isoformat(),"dashboard_counts":self.db.dashboard_counts(),"health":health,"privacy":privacy,"recent_security_events":self.db.list_security_logs(30),"recent_devices":self.db.list_device_events(30)}
        EXPORTS_DIR.mkdir(parents=True,exist_ok=True); path=EXPORTS_DIR/f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"; path.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf-8'); return path
    def delete_user_generated_data(self,user_id: int,categories: list[str])->dict[str,int]:
        allowed={"translations":"created_by","ai_history":"user_id","command_history":"user_id","reminders":"user_id","notifications":"user_id","meetings":"created_by"}; result={}
        for table in categories:
            if table not in allowed: continue
            before=self.db.fetch_one(f"SELECT COUNT(*) AS total FROM {table} WHERE {allowed[table]}={self.db.p}",(user_id,)); self.db.execute(f"DELETE FROM {table} WHERE {allowed[table]}={self.db.p}",(user_id,)); result[table]=int(before['total'] if before else 0)
        return result
