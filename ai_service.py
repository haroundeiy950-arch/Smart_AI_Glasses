"""Ask AI Text: cloud AI when explicitly enabled, useful offline troubleshooting otherwise."""
from __future__ import annotations
import os,platform,sys
from dataclasses import dataclass
from typing import Any
from config import AI_ENABLED,OPENAI_API_KEY,OPENAI_MODEL,PROJECT_NAME
from database import DatabaseManager
from logger import get_logger
from privacy_manager import PrivacyManager

log=get_logger("ai")

@dataclass(slots=True)
class AIAnswer:
    answer: str
    provider: str

class AIService:
    def __init__(self,database: DatabaseManager,privacy: PrivacyManager): self.db=database; self.privacy=privacy
    def _offline_answer(self,question: str,context: dict[str,Any]|None=None)->str:
        q=question.lower().strip(); context=context or {}
        rules=[
            (("unknown","غير معروف","ما اعرف","ntamuzi"),"لا يمكن للنظام معرفة اسم شخص غير مسجل بشكل موثوق. خذ موافقته، افتح Vision > Register Person، التقط العينات، درّب Face Model، ثم اربطه بالحساب عند الحاجة إلى Face Unlock."),
            (("cv2","opencv","camera","كاميرا"),"افتح System Health. ثبّت opencv-contrib-python داخل البيئة نفسها، أغلق Zoom وCamera وTeams، ثم جرّب CAMERA_INDEX من 0 إلى 3 داخل .env."),
            (("cv2.face","lbph"),"خاصية cv2.face موجودة في opencv-contrib-python فقط. احذف opencv-python ثم ثبّت opencv-contrib-python."),
            (("deepface","emotion","مشاعر"),"DeepFace اختياري. استخدم Python 3.11 وثبّت requirements-ai.txt. تحليل المشاعر مؤشر تقريبي وليس حكمًا نهائيًا."),
            (("translate","ترجم","translation","kinyarwanda","ikinyarwanda"),"افتح Translation، اختر لغة المصدر والهدف rw — Kinyarwanda. العبارات الأساسية تعمل محليًا، والترجمة العامة تحتاج الإنترنت."),
            (("microphone","مايكروفون","pyaudio"),"يمكنك استخدام النص اليدوي بدون مايكروفون. للتسجيل المباشر ثبّت PyAudio وفعّل Microphone وMeeting Recording من Privacy."),
            (("login","password","كلمة المرور","username"),"الحساب الأول admin وكلمة المرور المؤقتة Admin@12345. غيّرها من Security. يمكن ربط وجه مسجل بحساب لتفعيل Face Unlock."),
            (("yolo","object detection","اكتشاف الأشياء"),"ثبّت requirements-ai.txt. أول تشغيل قد ينزّل نموذج YOLO. افتح Vision ثم YOLO Object Detection."),
            (("ocr","tesseract","قراءة النص"),"ثبّت برنامج Tesseract على Windows ثم ضع TESSERACT_CMD في .env. لإضافة العربية ثبّت ara.traineddata واستخدم OCR_LANGUAGES=ara+eng+fra."),
            (("backup","نسخة احتياطية","نسخ احتياطي"),"افتح Data Control ثم Create Backup. يمكن إنشاء ZIP عادي أو نسخة مشفرة إذا كانت مكتبة cryptography مثبتة."),
        ]
        for keys,answer in rules:
            if any(k in q for k in keys): return answer
        return f"أنا المساعد الداخلي لمشروع {PROJECT_NAME}. حالة النظام: {context.get('health_summary','غير متوفرة')}. أستطيع شرح الكاميرا، الوجوه، الترجمة، Kinyarwanda، OCR، الاجتماعات، الأمان، النسخ الاحتياطي والمكتبات. اكتب الخطأ كما ظهر كاملًا."
    def ask(self,question: str,*,context: dict[str,Any]|None=None,context_type: str="general",user_id: int|None=None)->AIAnswer:
        question=question.strip()
        if not question: raise ValueError("Enter a question for Ask AI")
        cloud=AI_ENABLED and bool(OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")) and self.privacy.get_permissions().get("cloud_ai",False)
        if cloud:
            try:
                from openai import OpenAI
                client=OpenAI(api_key=OPENAI_API_KEY or os.getenv("OPENAI_API_KEY"))
                system_context={"project":PROJECT_NAME,"python":sys.version.split()[0],"os":platform.platform(),**(context or {})}
                prompt=("You are the integrated technical assistant for a Python smart-glasses system. Reply in the user's language. "
                        "Give practical steps, preserve privacy, never guess an unknown person's identity, and do not treat emotion estimation as fact. "
                        f"System context: {system_context}\nUser: {question}")
                response=client.responses.create(model=OPENAI_MODEL,input=prompt)
                answer=response.output_text.strip(); provider=f"openai/{OPENAI_MODEL}"
            except Exception as exc:
                log.warning("Cloud AI failed: %s",exc); answer=self._offline_answer(question,context)+f"\n\nCloud AI error: {exc}"; provider="offline-fallback"
        else:
            answer=self._offline_answer(question,context); provider="offline-rules"
        self.db.add_ai_history(question,answer,provider,context_type,user_id); return AIAnswer(answer,provider)
