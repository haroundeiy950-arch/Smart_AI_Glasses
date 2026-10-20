"""Per-user privacy permission manager."""
from __future__ import annotations
from typing import Any
from config import DEFAULT_PRIVACY
from database import DatabaseManager

class PrivacyManager:
    def __init__(self,database: DatabaseManager): self.db=database; self.user_id: int|None=None
    def set_user(self,user_id: int|None): self.user_id=user_id
    def get_permissions(self)->dict[str,bool]:
        saved=self.db.get_setting("privacy_permissions",self.user_id,{}) or {}
        return {**DEFAULT_PRIVACY,**{k:bool(v) for k,v in saved.items()}}
    def set_permission(self,key: str,enabled: bool)->None:
        if key not in DEFAULT_PRIVACY: raise KeyError(f"Unknown privacy permission: {key}")
        data=self.get_permissions(); data[key]=bool(enabled); self.db.set_setting("privacy_permissions",data,self.user_id)
    def update(self,permissions: dict[str,bool])->None:
        data=self.get_permissions()
        for key,value in permissions.items():
            if key in DEFAULT_PRIVACY: data[key]=bool(value)
        self.db.set_setting("privacy_permissions",data,self.user_id)
    def require(self,key: str)->None:
        if not self.get_permissions().get(key,False): raise PermissionError(f"Privacy permission '{key}' is disabled")
    def export(self)->dict[str,Any]: return {"user_id":self.user_id,"permissions":self.get_permissions()}
