"""Central command router connecting every project capability."""
from __future__ import annotations
import re
from typing import Any
from ai_service import AIService
from database import DatabaseManager
from reminder_service import ReminderService
from translator_service import TranslatorService

class AssistantCore:
    def __init__(self,translator: TranslatorService,ai_service: AIService,reminders: ReminderService,database: DatabaseManager,controller: Any|None=None): self.translator=translator; self.ai=ai_service; self.reminders=reminders; self.db=database; self.controller=controller
    def set_controller(self,controller: Any): self.controller=controller
    def handle_text_command(self,command: str,user_id: int|None=None)->str:
        text=command.strip(); lower=text.lower(); response=""; kind="ai"
        if not text: return "اكتب أمرًا أو سؤالًا."
        if lower in {"health","system health","حالة النظام","status"} and self.controller:
            health=self.controller.health_check(quick=True); response="\n".join(f"{n}: {v['status']} - {v['message']}" for n,v in health.items()); kind="health"
        elif lower.startswith(("translate:","ترجم:")):
            payload=text.split(':',1)[1].strip(); response=self.translator.translate(payload,"auto","rw",user_id).translated_text; kind="translation"
        elif lower.startswith(("remind:","ذكرني:")) and user_id:
            payload=text.split(':',1)[1].strip(); self.reminders.add(user_id,payload); response=f"تم حفظ التذكير: {payload}"; kind="reminder"
        elif any(k in lower for k in ("who is this","من هذا الشخص","uyu ni nde")):
            response="open Vision ثم Live Face Recognition. لن أخمّن هوية شخص غير مسجل."; kind="vision"
        elif lower in {"open camera","افتح الكاميرا","fungura camera"} and self.controller:
            response="تم إرسال أمر فتح الكاميرا. أغلق النافذة بالضغط على Q."; kind="camera"; self.controller.camera.preview()
        else:
            context=self.controller.ai_context() if self.controller else {}; response=self.ai.ask(text,context=context,context_type="assistant",user_id=user_id).answer
        self.db.add_command_history(text,response,kind,user_id); return response
