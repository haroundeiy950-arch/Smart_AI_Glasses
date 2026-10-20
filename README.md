# Smart AI Glasses System — Complete Professional Edition 2.0

مشروع سطح مكتب احترافي بلغة **Python** يحاكي نظام التحكم الكامل للنظارات الذكية، ويربط الكاميرا، التعرف على الأشخاص، اكتشاف الأشياء، OCR، الترجمة، الصوت، الاجتماعات، Ask AI، تسجيل الدخول، الخصوصية، التذكيرات، الأجهزة، النسخ الاحتياطي والتصدير من خلال ملف مركزي واحد هو `control_system.py`.

> المشروع البرمجي كامل وقابل للتشغيل على الكمبيوتر. تحويله إلى نظارة Hardware حقيقية يحتاج لاحقًا إلى كاميرا صغيرة، مايكروفون، سماعة، شاشة HUD، بطارية، لوحة Raspberry Pi أو وحدة مشابهة، ومرحلة Firmware منفصلة.

## أهم الوظائف الموجودة فعليًا

### 1. تسجيل الدخول والأمان

- Username + Password.
- حساب مدير افتراضي.
- تشفير كلمة المرور باستخدام PBKDF2 مع Salt.
- قفل مؤقت بعد محاولات الدخول الفاشلة.
- أدوار: `admin` و`user` و`viewer`.
- إنشاء مستخدمين وتفعيلهم أو تعطيلهم.
- تغيير كلمة المرور.
- سجل أمني كامل.
- **Face Unlock حقيقي** بعد تسجيل وجه الشخص وربطه بحسابه وتدريب النموذج.
- تشفير النصوص والنسخ الاحتياطية باستخدام Fernet عند توفر `cryptography`.

### 2. Control System

`control_system.py` هو عقل الربط التشغيلي. يقوم بإنشاء وربط:

- قاعدة البيانات.
- Security وPrivacy.
- Camera وFace Recognition.
- YOLO وOCR وEmotion.
- Speech-to-Text وText-to-Speech.
- Translation.
- Meeting Assistant.
- Ask AI وAssistant Commands.
- Notifications وReminders.
- Device Manager.
- Backup Manager وData Control.
- System Health.

### 3. الكاميرا والرؤية

- البحث تلقائيًا عن الكاميرا في الفهارس 0 و1 و2 و3.
- معاينة الكاميرا والتقاط الصور.
- تسجيل شخص من الكاميرا مع 30 عينة افتراضيًا.
- تدريب OpenCV LBPH.
- التعرف على الأشخاص مباشرة في الوقت الحقيقي.
- عرض الاسم وMatch Score تقريبي.
- اكتشاف الشخص غير المعروف.
- حفظ صورة الشخص المجهول فقط عند تفعيل إذن الخصوصية.
- مراجعة وحذف أحداث الأشخاص المجهولين.
- ربط وجه مسجل بحساب Login لتفعيل Face Unlock.
- اكتشاف الأشياء باستخدام YOLO.
- OCR من صورة ملتقطة أو من الكاميرا المباشرة.
- تحليل تعبيرات الوجه اختياريًا باستخدام DeepFace.

### 4. اللغات والترجمة

يدعم النظام:

- العربية `ar`
- الإنجليزية `en`
- الفرنسية `fr`
- **Kinyarwanda `rw`**
- السواحيلية `sw`
- الإسبانية، الألمانية، البرتغالية، الإيطالية، التركية، الصينية والهندية.

المتوفر:

- ترجمة النصوص.
- إدخال صوتي ثم ترجمة.
- قراءة الترجمة صوتيًا.
- سجل ترجمة داخل قاعدة البيانات.
- عرض الترجمة داخل نافذة HUD تحاكي شاشة النظارة الصغيرة.
- قاموس عبارات أساسية يعمل Offline بين الإنجليزية والعربية وKinyarwanda.
- الترجمة العامة عبر الإنترنت باستخدام `deep-translator`.

### 5. الاجتماعات والمحاضرات

- بدء جلسة اجتماع.
- حفظ العنوان والمشاركين واللغة.
- التحقق من موافقة المشاركين.
- إضافة الكلام يدويًا.
- الاستماع إلى مقطع كلام واحد من المايكروفون.
- **ترجمة كل مقطع مباشرة داخل جلسة الاجتماع**.
- تسجيل صوت WAV اختياريًا باستخدام PyAudio.
- حفظ النص الأصلي والترجمة.
- تلخيص الاجتماع.
- استخراج القرارات.
- استخراج المهام والمسؤوليات.
- حفظ الاجتماع في SQLite/MySQL وملف JSON.
- عرض سجل الاجتماعات.
- تصدير اجتماع إلى TXT أو JSON.
- حذف الاجتماعات.

### 6. Ask AI Text والمساعد الذكي

- Ask AI Text مربوط بحالة النظام، الخصوصية، قاعدة البيانات، عدد الأشخاص والاجتماعات.
- مساعد Offline يحل الأخطاء الشائعة حتى بدون API.
- يشرح أخطاء OpenCV وDeepFace وYOLO وTesseract والمايكروفون والترجمة وتسجيل الدخول.
- لا يخمن هوية شخص غير معروف.
- يدعم أوامر مثل:
  - `حالة النظام`
  - `ترجم: صباح الخير`
  - `ذكرني: الاجتماع غدًا`
  - `من هذا الشخص؟`
- يمكن ربطه اختياريًا بخدمة OpenAI عند وضع المفتاح وتفعيل إذن Cloud AI.
- يحفظ سجل الأسئلة والأجوبة والأوامر.

### 7. تحليل المشاعر ونبرة الصوت

- تحليل تعبير الوجه اختياريًا عبر DeepFace.
- تحليل Tone للنص بطريقة Heuristic.
- تحليل مؤشرات ملف WAV مثل الطاقة وZero Crossing Rate.
- النتائج مؤشرات تقريبية فقط وليست تشخيصًا أو حكمًا على الشخص.

### 8. Data Control

- مزامنة المستخدمين إلى `data/users.json` بدون كلمات المرور أو Salt.
- تصدير جداول CSV.
- تصدير جميع البيانات إلى JSON.
- إنشاء System Report.
- إنشاء ZIP Backup.
- خيار تضمين الصور والصوت.
- خيار تشفير النسخة الاحتياطية.
- استعادة Backup.
- إدارة التذكيرات.
- فحص الكاميرا والمايكروفونات وText-to-Speech.
- حفظ Device History.
- الإشعارات داخل النظام.

## هيكل المشروع

```text
Smart_AI_Glasses_Complete/
├── main.py
├── config.py
├── database.py
├── control_system.py
├── data_control.py
├── camera_service.py
├── object_detector.py
├── face_identifier.py
├── ocr_reader.py
├── speech_to_text.py
├── text_to_speech.py
├── audio_recorder.py
├── translator_service.py
├── emotion_analyzer.py
├── meeting_assistant.py
├── ai_service.py
├── assistant_core.py
├── security.py
├── privacy_manager.py
├── notification_service.py
├── reminder_service.py
├── device_manager.py
├── backup_manager.py
├── hud_display.py
├── i18n.py
├── ui.py
├── logger.py
├── requirements.txt
├── requirements-ai.txt
├── requirements-audio.txt
├── .env.example
├── run_windows.bat
├── install_ai_windows.bat
├── install_audio_windows.bat
├── FEATURE_CHECKLIST.md
├── data/
│   ├── users.json
│   ├── smart_ai_glasses.db
│   ├── known_faces/
│   ├── meetings/
│   ├── translations/
│   ├── backups/
│   └── exports/
├── models/
│   ├── object_detection/
│   ├── face_models/
│   ├── emotion_models/
│   └── speech_models/
├── images/
│   ├── captured/
│   ├── samples/
│   └── unknown/
├── sounds/
│   ├── recorded/
│   └── output_voice/
├── logs/
└── tests/
```

## التشغيل على Windows

يفضل استخدام **Python 3.11** لأن DeepFace وTensorFlow وبعض مكتبات الصوت قد تواجه مشاكل في Python 3.14.

```powershell
cd "PATH\TO\Smart_AI_Glasses_Complete"
py -3.11 -m venv venv311
venv311\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

أو شغّل:

```text
run_windows.bat
```

## بيانات الدخول الأولى

```text
Username: admin
Password: Admin@12345
```

غيّر كلمة المرور مباشرة من Security.

## تثبيت YOLO وDeepFace

```powershell
venv311\Scripts\activate
python -m pip install -r requirements-ai.txt
```

## تثبيت تسجيل صوت الاجتماعات

```powershell
python -m pip install -r requirements-audio.txt
```

إذا فشل PyAudio، تظل الاجتماعات تعمل بالنص اليدوي وSpeechRecognition دون تسجيل WAV مباشر.

## إعداد Tesseract OCR

ثبت برنامج Tesseract على Windows، ثم انسخ `.env.example` إلى `.env` وتأكد من المسار:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_LANGUAGES=ara+eng+fra
```

## استخدام MySQL بدل SQLite

```env
DB_ENGINE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=YOUR_PASSWORD
MYSQL_DATABASE=smart_ai_glasses
```

SQLite هو الوضع الافتراضي والأسهل للتشغيل.

## إعداد Ask AI Cloud

في `.env`:

```env
OPENAI_API_KEY=YOUR_KEY
OPENAI_MODEL=gpt-4.1-mini
```

بعد تسجيل الدخول افتح Settings وفعّل Cloud AI. بدون الإذن لا يتم إرسال النص إلى الخدمة السحابية، ويستمر المساعد Offline.

## خطوات Face Unlock الصحيحة

1. سجل الدخول بكلمة المرور.
2. Settings: فعّل Camera وFace Recognition.
3. Vision: اختر Register Person.
4. خذ موافقة الشخص وسجل الصور.
5. اضغط Train Face Model.
6. حدد الشخص من القائمة واضغط Link to Current User.
7. سجل الخروج.
8. اكتب Username ثم اضغط Face Unlock.

## أوامر الفحص والاختبار

```powershell
python main.py --health
python main.py --full-health
python -m unittest discover -s tests -v
```

تم تشغيل **13 اختبارًا آليًا بنجاح** على طبقات قاعدة البيانات، الأمان، الخصوصية، الترجمة، Kinyarwanda، الاجتماعات، Ask AI، الكاميرا، الصوت وData Control.

## ملاحظات مهمة

- لا تحفظ صور أو أصوات الأشخاص دون موافقة واضحة.
- YOLO لا يتعرف على كل شيء؛ الأنواع تعتمد على النموذج المستخدم.
- LBPH يعيد Distance وليس احتمالًا حقيقيًا، لذلك Match Score تقريبي.
- DeepFace وتحليل النبرة لا يحددان حقيقة مشاعر الشخص.
- وظائف Google Translation وGoogle Speech Recognition تحتاج الإنترنت.
- هذه نسخة Software Desktop متكاملة؛ ربط Hardware الحقيقي مرحلة تالية.
