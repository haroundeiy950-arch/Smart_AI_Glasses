"""In-app notifications for security, meetings, reminders and system events."""
from __future__ import annotations
from database import DatabaseManager
from privacy_manager import PrivacyManager

class NotificationService:
    def __init__(self,database: DatabaseManager,privacy: PrivacyManager): self.db=database; self.privacy=privacy
    def notify(self,title: str,message: str,category: str="system",user_id: int|None=None)->int|None:
        if not self.privacy.get_permissions().get('notifications',True): return None
        return self.db.add_notification(user_id,category,title,message)
    def list(self,user_id: int|None,unread_only: bool=False): return self.db.list_notifications(user_id,unread_only)
    def mark_read(self,notification_id: int): self.db.mark_notification_read(notification_id)
