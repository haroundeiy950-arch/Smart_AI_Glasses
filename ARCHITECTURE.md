# Architecture

```text
UI / HUD
   |
SystemController
   |-- Security + Privacy
   |-- Database + DataControl + Backup
   |-- Camera
   |    |-- FaceIdentifier
   |    |-- ObjectDetector
   |    |-- OCRReader
   |    `-- EmotionAnalyzer
   |-- SpeechToText + TextToSpeech + AudioRecorder
   |-- TranslatorService
   |-- MeetingAssistant
   |-- AIService + AssistantCore
   |-- NotificationService + ReminderService
   `-- DeviceManager + Health Check
```

كل خدمة مستقلة ويمكن اختبارها منفردة. المكتبات الثقيلة يتم استيرادها Lazy حتى لا يتوقف المشروع كله عند غياب YOLO أو DeepFace أو PyAudio.
