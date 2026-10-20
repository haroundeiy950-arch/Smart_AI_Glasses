"""Repository layer. SQLite works immediately; MySQL is optional through .env."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from config import DB_ENGINE, MYSQL_DATABASE, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT, MYSQL_USER, SQLITE_PATH, ensure_project_folders
from logger import get_logger

log = get_logger(__name__)

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

class DatabaseManager:
    def __init__(self, engine: str | None = None, db_path: str | Path | None = None) -> None:
        ensure_project_folders()
        self.engine = (engine or DB_ENGINE).lower()
        self.db_path = Path(db_path) if db_path else SQLITE_PATH
        if self.engine not in {"sqlite", "mysql"}:
            raise ValueError("DB_ENGINE must be sqlite or mysql")
        self.initialize()

    @property
    def p(self) -> str:
        return "?" if self.engine == "sqlite" else "%s"

    def _mysql_connection(self):
        try:
            import mysql.connector
        except ImportError as exc:
            raise RuntimeError("Install mysql-connector-python for MySQL support") from exc
        bootstrap = mysql.connector.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD)
        try:
            safe = "".join(ch for ch in MYSQL_DATABASE if ch.isalnum() or ch == "_")
            if not safe:
                raise ValueError("Invalid MYSQL_DATABASE")
            cur = bootstrap.cursor()
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{safe}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            bootstrap.commit()
        finally:
            bootstrap.close()
        return mysql.connector.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE)

    @contextmanager
    def connection(self) -> Iterator[Any]:
        if self.engine == "sqlite":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA journal_mode=WAL")
        else:
            conn = self._mysql_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _schema(self) -> list[str]:
        pk = "INTEGER PRIMARY KEY AUTOINCREMENT" if self.engine == "sqlite" else "INT PRIMARY KEY AUTO_INCREMENT"
        b = "INTEGER" if self.engine == "sqlite" else "TINYINT(1)"
        return [
            f"""CREATE TABLE IF NOT EXISTS users(
                id {pk}, username VARCHAR(80) NOT NULL UNIQUE, password_hash TEXT NOT NULL, salt TEXT NOT NULL,
                full_name VARCHAR(160) NOT NULL, role VARCHAR(40) NOT NULL DEFAULT 'user', preferred_language VARCHAR(20) NOT NULL DEFAULT 'ar',
                is_active {b} NOT NULL DEFAULT 1, failed_attempts INTEGER NOT NULL DEFAULT 0, locked_until VARCHAR(50),
                created_at VARCHAR(50) NOT NULL, updated_at VARCHAR(50) NOT NULL, last_login VARCHAR(50))""",
            f"""CREATE TABLE IF NOT EXISTS known_people(
                id {pk}, person_code VARCHAR(80) NOT NULL UNIQUE, name VARCHAR(160) NOT NULL, job_title VARCHAR(160), phone VARCHAR(80),
                notes TEXT, folder_path TEXT NOT NULL, consent {b} NOT NULL DEFAULT 0, linked_user_id INTEGER,
                created_at VARCHAR(50) NOT NULL, updated_at VARCHAR(50) NOT NULL,
                FOREIGN KEY(linked_user_id) REFERENCES users(id) ON DELETE SET NULL)""",
            f"""CREATE TABLE IF NOT EXISTS unknown_events(
                id {pk}, image_path TEXT, match_score REAL, camera_name VARCHAR(80), reviewed {b} NOT NULL DEFAULT 0,
                notes TEXT, created_at VARCHAR(50) NOT NULL)""",
            f"""CREATE TABLE IF NOT EXISTS translations(
                id {pk}, source_text TEXT NOT NULL, translated_text TEXT NOT NULL, source_language VARCHAR(20), target_language VARCHAR(20),
                provider VARCHAR(50), created_by INTEGER, created_at VARCHAR(50) NOT NULL, FOREIGN KEY(created_by) REFERENCES users(id))""",
            f"""CREATE TABLE IF NOT EXISTS meetings(
                id {pk}, title VARCHAR(220) NOT NULL, participants TEXT, source_language VARCHAR(20), target_language VARCHAR(20),
                transcript TEXT, translated_transcript TEXT, summary TEXT, decisions TEXT, tasks TEXT, audio_path TEXT,
                consent_confirmed {b} NOT NULL DEFAULT 0, status VARCHAR(30) NOT NULL DEFAULT 'completed',
                started_at VARCHAR(50) NOT NULL, ended_at VARCHAR(50), created_by INTEGER, FOREIGN KEY(created_by) REFERENCES users(id))""",
            f"""CREATE TABLE IF NOT EXISTS meeting_notes(
                id {pk}, meeting_id INTEGER NOT NULL, note TEXT NOT NULL, speaker VARCHAR(160), language VARCHAR(20), created_at VARCHAR(50) NOT NULL,
                FOREIGN KEY(meeting_id) REFERENCES meetings(id) ON DELETE CASCADE)""",
            f"""CREATE TABLE IF NOT EXISTS security_logs(
                id {pk}, user_id INTEGER, event_type VARCHAR(100) NOT NULL, severity VARCHAR(20) NOT NULL DEFAULT 'INFO',
                message TEXT NOT NULL, metadata TEXT, created_at VARCHAR(50) NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id))""",
            f"""CREATE TABLE IF NOT EXISTS ai_history(
                id {pk}, user_id INTEGER, question TEXT NOT NULL, answer TEXT NOT NULL, provider VARCHAR(60) NOT NULL,
                context_type VARCHAR(50), created_at VARCHAR(50) NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id))""",
            f"""CREATE TABLE IF NOT EXISTS settings(
                id {pk}, user_id INTEGER, setting_key VARCHAR(120) NOT NULL, setting_value TEXT NOT NULL, updated_at VARCHAR(50) NOT NULL,
                UNIQUE(user_id, setting_key), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)""",
            f"""CREATE TABLE IF NOT EXISTS reminders(
                id {pk}, user_id INTEGER, title VARCHAR(220) NOT NULL, due_at VARCHAR(50), notes TEXT, completed {b} NOT NULL DEFAULT 0,
                created_at VARCHAR(50) NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)""",
            f"""CREATE TABLE IF NOT EXISTS notifications(
                id {pk}, user_id INTEGER, category VARCHAR(50), title VARCHAR(220) NOT NULL, message TEXT NOT NULL,
                is_read {b} NOT NULL DEFAULT 0, created_at VARCHAR(50) NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)""",
            f"""CREATE TABLE IF NOT EXISTS device_events(
                id {pk}, device_type VARCHAR(80), device_name VARCHAR(180), status VARCHAR(50), details TEXT, created_at VARCHAR(50) NOT NULL)""",
            f"""CREATE TABLE IF NOT EXISTS command_history(
                id {pk}, user_id INTEGER, command_text TEXT NOT NULL, response_text TEXT, command_type VARCHAR(50), created_at VARCHAR(50) NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL)""",
        ]

    def initialize(self) -> None:
        with self.connection() as conn:
            cur = conn.cursor()
            for sql in self._schema():
                cur.execute(sql)
        log.info("Database ready: %s", self.engine)

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self.connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return int(cur.lastrowid or 0)

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            if row is None:
                return None
            if self.engine == "sqlite":
                return dict(row)
            cols = [x[0] for x in cur.description]
            return dict(zip(cols, row))

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if self.engine == "sqlite":
                return [dict(r) for r in rows]
            cols = [x[0] for x in cur.description]
            return [dict(zip(cols, r)) for r in rows]

    # users
    def create_user(self, username: str, password_hash: str, salt: str, full_name: str, role: str = "user", preferred_language: str = "ar") -> int:
        p = self.p; now = utc_now()
        return self.execute(f"INSERT INTO users(username,password_hash,salt,full_name,role,preferred_language,created_at,updated_at) VALUES({p},{p},{p},{p},{p},{p},{p},{p})", (username,password_hash,salt,full_name,role,preferred_language,now,now))
    def get_user_by_username(self, username: str):
        return self.fetch_one(f"SELECT * FROM users WHERE username={self.p}", (username,))
    def get_user(self, user_id: int):
        return self.fetch_one(f"SELECT * FROM users WHERE id={self.p}", (user_id,))
    def list_users(self):
        return self.fetch_all("SELECT id,username,full_name,role,preferred_language,is_active,failed_attempts,locked_until,created_at,last_login FROM users ORDER BY id")
    def update_login_state(self, user_id: int, failed_attempts: int = 0, locked_until: str | None = None, success: bool = False):
        p = self.p
        if success:
            self.execute(f"UPDATE users SET failed_attempts=0,locked_until=NULL,last_login={p},updated_at={p} WHERE id={p}", (utc_now(),utc_now(),user_id))
        else:
            self.execute(f"UPDATE users SET failed_attempts={p},locked_until={p},updated_at={p} WHERE id={p}", (failed_attempts,locked_until,utc_now(),user_id))
    def update_password(self, user_id: int, password_hash: str, salt: str):
        p=self.p; self.execute(f"UPDATE users SET password_hash={p},salt={p},updated_at={p} WHERE id={p}",(password_hash,salt,utc_now(),user_id))
    def set_user_active(self, user_id: int, active: bool):
        p=self.p; self.execute(f"UPDATE users SET is_active={p},updated_at={p} WHERE id={p}",(1 if active else 0,utc_now(),user_id))

    # people
    def upsert_known_person(self, person_code: str, name: str, job_title: str, phone: str, notes: str, folder_path: str, consent: bool, linked_user_id: int | None = None) -> int:
        existing=self.get_known_person_by_code(person_code); p=self.p; now=utc_now()
        if existing:
            self.execute(f"UPDATE known_people SET name={p},job_title={p},phone={p},notes={p},folder_path={p},consent={p},linked_user_id={p},updated_at={p} WHERE id={p}",(name,job_title,phone,notes,folder_path,1 if consent else 0,linked_user_id,now,existing['id']))
            return int(existing['id'])
        return self.execute(f"INSERT INTO known_people(person_code,name,job_title,phone,notes,folder_path,consent,linked_user_id,created_at,updated_at) VALUES({p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",(person_code,name,job_title,phone,notes,folder_path,1 if consent else 0,linked_user_id,now,now))
    def get_known_person_by_code(self, code: str):
        return self.fetch_one(f"SELECT * FROM known_people WHERE person_code={self.p}",(code,))
    def get_known_person(self, person_id: int):
        return self.fetch_one(f"SELECT * FROM known_people WHERE id={self.p}",(person_id,))
    def list_known_people(self):
        return self.fetch_all("SELECT * FROM known_people ORDER BY name")
    def delete_known_person(self, person_id: int):
        self.execute(f"DELETE FROM known_people WHERE id={self.p}",(person_id,))
    def link_person_to_user(self, person_id: int, user_id: int | None):
        self.execute(f"UPDATE known_people SET linked_user_id={self.p},updated_at={self.p} WHERE id={self.p}",(user_id,utc_now(),person_id))
    def get_person_for_user(self, user_id: int):
        return self.fetch_one(f"SELECT * FROM known_people WHERE linked_user_id={self.p}",(user_id,))

    # unknown
    def add_unknown_event(self, image_path: str, match_score: float | None, camera_name: str = "camera") -> int:
        p=self.p; return self.execute(f"INSERT INTO unknown_events(image_path,match_score,camera_name,created_at) VALUES({p},{p},{p},{p})",(image_path,match_score,camera_name,utc_now()))
    def list_unknown_events(self, limit: int = 200):
        return self.fetch_all(f"SELECT * FROM unknown_events ORDER BY id DESC LIMIT {int(limit)}")
    def review_unknown_event(self, event_id: int, notes: str = ""):
        p=self.p; self.execute(f"UPDATE unknown_events SET reviewed=1,notes={p} WHERE id={p}",(notes,event_id))
    def delete_unknown_event(self, event_id: int):
        self.execute(f"DELETE FROM unknown_events WHERE id={self.p}",(event_id,))

    # translations
    def add_translation(self, source_text: str, translated_text: str, source_language: str, target_language: str, provider: str, user_id: int | None) -> int:
        p=self.p; return self.execute(f"INSERT INTO translations(source_text,translated_text,source_language,target_language,provider,created_by,created_at) VALUES({p},{p},{p},{p},{p},{p},{p})",(source_text,translated_text,source_language,target_language,provider,user_id,utc_now()))
    def list_translations(self, user_id: int | None = None, limit: int = 200):
        if user_id is None: return self.fetch_all(f"SELECT * FROM translations ORDER BY id DESC LIMIT {int(limit)}")
        return self.fetch_all(f"SELECT * FROM translations WHERE created_by={self.p} ORDER BY id DESC LIMIT {int(limit)}",(user_id,))

    # meetings
    def create_meeting(self, title: str, participants: list[str], source_language: str, target_language: str, transcript: str, translated_transcript: str, summary: str, decisions: list[str], tasks: list[str], audio_path: str | None, consent: bool, created_by: int | None, started_at: str | None = None, ended_at: str | None = None) -> int:
        p=self.p
        return self.execute(f"INSERT INTO meetings(title,participants,source_language,target_language,transcript,translated_transcript,summary,decisions,tasks,audio_path,consent_confirmed,status,started_at,ended_at,created_by) VALUES({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",(title,json.dumps(participants,ensure_ascii=False),source_language,target_language,transcript,translated_transcript,summary,json.dumps(decisions,ensure_ascii=False),json.dumps(tasks,ensure_ascii=False),audio_path,1 if consent else 0,"completed",started_at or utc_now(),ended_at or utc_now(),created_by))
    def list_meetings(self, limit: int = 200):
        return self.fetch_all(f"SELECT * FROM meetings ORDER BY id DESC LIMIT {int(limit)}")
    def get_meeting(self, meeting_id: int):
        return self.fetch_one(f"SELECT * FROM meetings WHERE id={self.p}",(meeting_id,))
    def delete_meeting(self, meeting_id: int):
        self.execute(f"DELETE FROM meetings WHERE id={self.p}",(meeting_id,))
    def add_meeting_note(self, meeting_id: int, note: str, speaker: str = "", language: str = ""):
        p=self.p; return self.execute(f"INSERT INTO meeting_notes(meeting_id,note,speaker,language,created_at) VALUES({p},{p},{p},{p},{p})",(meeting_id,note,speaker,language,utc_now()))

    # logs and AI
    def add_security_log(self, event_type: str, message: str, severity: str = "INFO", user_id: int | None = None, metadata: dict[str,Any] | None = None):
        p=self.p; return self.execute(f"INSERT INTO security_logs(user_id,event_type,severity,message,metadata,created_at) VALUES({p},{p},{p},{p},{p},{p})",(user_id,event_type,severity,message,json.dumps(metadata or {},ensure_ascii=False),utc_now()))
    def list_security_logs(self, limit: int = 300):
        return self.fetch_all(f"SELECT * FROM security_logs ORDER BY id DESC LIMIT {int(limit)}")
    def add_ai_history(self, question: str, answer: str, provider: str, context_type: str, user_id: int | None):
        p=self.p; return self.execute(f"INSERT INTO ai_history(user_id,question,answer,provider,context_type,created_at) VALUES({p},{p},{p},{p},{p},{p})",(user_id,question,answer,provider,context_type,utc_now()))
    def list_ai_history(self, user_id: int | None = None, limit: int = 100):
        if user_id is None: return self.fetch_all(f"SELECT * FROM ai_history ORDER BY id DESC LIMIT {int(limit)}")
        return self.fetch_all(f"SELECT * FROM ai_history WHERE user_id={self.p} ORDER BY id DESC LIMIT {int(limit)}",(user_id,))
    def add_command_history(self, command: str, response: str, command_type: str, user_id: int | None):
        p=self.p; return self.execute(f"INSERT INTO command_history(user_id,command_text,response_text,command_type,created_at) VALUES({p},{p},{p},{p},{p})",(user_id,command,response,command_type,utc_now()))

    # settings
    def set_setting(self, key: str, value: Any, user_id: int | None):
        p=self.p; encoded=json.dumps(value,ensure_ascii=False)
        row=self.fetch_one(f"SELECT id FROM settings WHERE setting_key={p} AND ((user_id={p}) OR (user_id IS NULL AND {p} IS NULL))",(key,user_id,user_id))
        if row: self.execute(f"UPDATE settings SET setting_value={p},updated_at={p} WHERE id={p}",(encoded,utc_now(),row['id']))
        else: self.execute(f"INSERT INTO settings(user_id,setting_key,setting_value,updated_at) VALUES({p},{p},{p},{p})",(user_id,key,encoded,utc_now()))
    def get_setting(self, key: str, user_id: int | None, default: Any = None):
        p=self.p; row=self.fetch_one(f"SELECT setting_value FROM settings WHERE setting_key={p} AND ((user_id={p}) OR (user_id IS NULL AND {p} IS NULL))",(key,user_id,user_id))
        if not row: return default
        try: return json.loads(row['setting_value'])
        except Exception: return row['setting_value']

    # reminders and notifications
    def add_reminder(self, user_id: int, title: str, due_at: str | None, notes: str = ""):
        p=self.p; return self.execute(f"INSERT INTO reminders(user_id,title,due_at,notes,created_at) VALUES({p},{p},{p},{p},{p})",(user_id,title,due_at,notes,utc_now()))
    def list_reminders(self, user_id: int):
        return self.fetch_all(f"SELECT * FROM reminders WHERE user_id={self.p} ORDER BY completed,due_at",(user_id,))
    def complete_reminder(self, reminder_id: int, completed: bool = True):
        self.execute(f"UPDATE reminders SET completed={self.p} WHERE id={self.p}",(1 if completed else 0,reminder_id))
    def add_notification(self, user_id: int | None, category: str, title: str, message: str):
        p=self.p; return self.execute(f"INSERT INTO notifications(user_id,category,title,message,created_at) VALUES({p},{p},{p},{p},{p})",(user_id,category,title,message,utc_now()))
    def list_notifications(self, user_id: int | None, unread_only: bool = False):
        where="WHERE (user_id IS NULL OR user_id="+self.p+")"; params=(user_id,)
        if unread_only: where += " AND is_read=0"
        return self.fetch_all(f"SELECT * FROM notifications {where} ORDER BY id DESC LIMIT 200",params)
    def mark_notification_read(self, notification_id: int):
        self.execute(f"UPDATE notifications SET is_read=1 WHERE id={self.p}",(notification_id,))
    def add_device_event(self, device_type: str, device_name: str, status: str, details: str):
        p=self.p; return self.execute(f"INSERT INTO device_events(device_type,device_name,status,details,created_at) VALUES({p},{p},{p},{p},{p})",(device_type,device_name,status,details,utc_now()))
    def list_device_events(self, limit: int = 100):
        return self.fetch_all(f"SELECT * FROM device_events ORDER BY id DESC LIMIT {int(limit)}")

    def dashboard_counts(self) -> dict[str,int]:
        tables=("known_people","meetings","translations","unknown_events","security_logs","reminders")
        out={}
        for table in tables:
            row=self.fetch_one(f"SELECT COUNT(*) AS total FROM {table}")
            out[table]=int(row['total'] if row else 0)
        return out
