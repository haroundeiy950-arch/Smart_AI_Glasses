"""Simple personal reminders used by the assistant."""
from __future__ import annotations
from datetime import datetime
from database import DatabaseManager

class ReminderService:
    def __init__(self,database: DatabaseManager): self.db=database
    def add(self,user_id: int,title: str,due_at: str|None=None,notes: str="")->int:
        if not title.strip(): raise ValueError("Reminder title is required")
        if due_at:
            try: datetime.fromisoformat(due_at)
            except ValueError as exc: raise ValueError("Use ISO date format: YYYY-MM-DD HH:MM") from exc
        return self.db.add_reminder(user_id,title.strip(),due_at,notes.strip())
    def list(self,user_id: int): return self.db.list_reminders(user_id)
    def complete(self,reminder_id: int,completed: bool=True): self.db.complete_reminder(reminder_id,completed)
