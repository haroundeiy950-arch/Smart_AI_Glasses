"""Central configuration for Smart AI Glasses System."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Final

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

BASE_DIR: Final[Path] = Path(__file__).resolve().parent
if load_dotenv:
    load_dotenv(BASE_DIR / ".env")

PROJECT_NAME: Final[str] = "Smart AI Glasses System"
PROJECT_VERSION: Final[str] = "2.0.0"
APP_MODE: str = os.getenv("APP_MODE", "development").lower()

DATA_DIR: Final[Path] = BASE_DIR / "data"
KNOWN_FACES_DIR: Final[Path] = DATA_DIR / "known_faces"
MEETINGS_DIR: Final[Path] = DATA_DIR / "meetings"
TRANSLATIONS_DIR: Final[Path] = DATA_DIR / "translations"
BACKUPS_DIR: Final[Path] = DATA_DIR / "backups"
EXPORTS_DIR: Final[Path] = DATA_DIR / "exports"
MODELS_DIR: Final[Path] = BASE_DIR / "models"
OBJECT_MODELS_DIR: Final[Path] = MODELS_DIR / "object_detection"
FACE_MODELS_DIR: Final[Path] = MODELS_DIR / "face_models"
EMOTION_MODELS_DIR: Final[Path] = MODELS_DIR / "emotion_models"
SPEECH_MODELS_DIR: Final[Path] = MODELS_DIR / "speech_models"
IMAGES_DIR: Final[Path] = BASE_DIR / "images"
CAPTURED_IMAGES_DIR: Final[Path] = IMAGES_DIR / "captured"
SAMPLES_DIR: Final[Path] = IMAGES_DIR / "samples"
UNKNOWN_IMAGES_DIR: Final[Path] = IMAGES_DIR / "unknown"
SOUNDS_DIR: Final[Path] = BASE_DIR / "sounds"
RECORDED_SOUNDS_DIR: Final[Path] = SOUNDS_DIR / "recorded"
OUTPUT_VOICE_DIR: Final[Path] = SOUNDS_DIR / "output_voice"
LOGS_DIR: Final[Path] = BASE_DIR / "logs"
TESTS_DIR: Final[Path] = BASE_DIR / "tests"

SQLITE_PATH: Path = Path(os.getenv("SQLITE_PATH", str(DATA_DIR / "smart_ai_glasses.db")))
DB_ENGINE: str = os.getenv("DB_ENGINE", "sqlite").lower()
MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "smart_ai_glasses")

CAMERA_INDEX: int = int(os.getenv("CAMERA_INDEX", "0"))
CAMERA_CANDIDATES: tuple[int, ...] = tuple(
    int(x.strip()) for x in os.getenv("CAMERA_CANDIDATES", "0,1,2,3").split(",") if x.strip()
)
CAMERA_WIDTH: int = int(os.getenv("CAMERA_WIDTH", "1280"))
CAMERA_HEIGHT: int = int(os.getenv("CAMERA_HEIGHT", "720"))
CAMERA_BACKEND: str = os.getenv("CAMERA_BACKEND", "auto").lower()

FACE_SAMPLE_COUNT: int = int(os.getenv("FACE_SAMPLE_COUNT", "30"))
FACE_SIZE: tuple[int, int] = (200, 200)
FACE_UNKNOWN_THRESHOLD: float = float(os.getenv("FACE_UNKNOWN_THRESHOLD", "75"))
FACE_CASCADE_PATH: Path = Path(os.getenv("FACE_CASCADE_PATH", str(FACE_MODELS_DIR / "haarcascade_frontalface_default.xml")))
FACE_MODEL_PATH: Path = Path(os.getenv("FACE_MODEL_PATH", str(FACE_MODELS_DIR / "lbph_face_model.yml")))
FACE_LABELS_PATH: Path = Path(os.getenv("FACE_LABELS_PATH", str(FACE_MODELS_DIR / "labels.json")))
UNKNOWN_CAPTURE_COOLDOWN_SECONDS: int = int(os.getenv("UNKNOWN_CAPTURE_COOLDOWN_SECONDS", "8"))

YOLO_MODEL: str = os.getenv("YOLO_MODEL", "yolo11n.pt")
YOLO_CONFIDENCE: float = float(os.getenv("YOLO_CONFIDENCE", "0.45"))
TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "")
OCR_LANGUAGES: str = os.getenv("OCR_LANGUAGES", "ara+eng+fra")

DEFAULT_UI_LANGUAGE: str = os.getenv("DEFAULT_UI_LANGUAGE", "ar")
DEFAULT_SOURCE_LANGUAGE: str = os.getenv("DEFAULT_SOURCE_LANGUAGE", "auto")
DEFAULT_TARGET_LANGUAGE: str = os.getenv("DEFAULT_TARGET_LANGUAGE", "rw")
LANGUAGES: Final[dict[str, dict[str, str]]] = {
    "auto": {"ar": "اكتشاف تلقائي", "en": "Auto Detect", "fr": "Détection auto", "rw": "Menya ururimi", "speech": ""},
    "ar": {"ar": "العربية", "en": "Arabic", "fr": "Arabe", "rw": "Icyarabu", "speech": "ar-SA"},
    "en": {"ar": "الإنجليزية", "en": "English", "fr": "Anglais", "rw": "Icyongereza", "speech": "en-US"},
    "fr": {"ar": "الفرنسية", "en": "French", "fr": "Français", "rw": "Igifaransa", "speech": "fr-FR"},
    "rw": {"ar": "كينيارواندا", "en": "Kinyarwanda", "fr": "Kinyarwanda", "rw": "Ikinyarwanda", "speech": "rw-RW"},
    "sw": {"ar": "السواحيلية", "en": "Swahili", "fr": "Swahili", "rw": "Igiswahili", "speech": "sw-KE"},
    "es": {"ar": "الإسبانية", "en": "Spanish", "fr": "Espagnol", "rw": "Icyesipanyolo", "speech": "es-ES"},
    "de": {"ar": "الألمانية", "en": "German", "fr": "Allemand", "rw": "Ikidage", "speech": "de-DE"},
    "pt": {"ar": "البرتغالية", "en": "Portuguese", "fr": "Portugais", "rw": "Igiporutugali", "speech": "pt-PT"},
    "it": {"ar": "الإيطالية", "en": "Italian", "fr": "Italien", "rw": "Igitaliyani", "speech": "it-IT"},
    "tr": {"ar": "التركية", "en": "Turkish", "fr": "Turc", "rw": "Igiturukiya", "speech": "tr-TR"},
    "zh-CN": {"ar": "الصينية", "en": "Chinese", "fr": "Chinois", "rw": "Igishinwa", "speech": "zh-CN"},
    "hi": {"ar": "الهندية", "en": "Hindi", "fr": "Hindi", "rw": "Igihindi", "speech": "hi-IN"},
}

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
AI_ENABLED: bool = os.getenv("AI_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
LOGIN_MAX_ATTEMPTS: int = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
LOCKOUT_MINUTES: int = int(os.getenv("LOCKOUT_MINUTES", "10"))
PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
ENCRYPTION_KEY_FILE: Path = Path(os.getenv("ENCRYPTION_KEY_FILE", str(DATA_DIR / ".secret.key")))

DEFAULT_PRIVACY: Final[dict[str, bool]] = {
    "camera": True,
    "microphone": False,
    "face_recognition": True,
    "save_unknown_faces": False,
    "meeting_recording": False,
    "cloud_ai": False,
    "location": False,
    "notifications": True,
}


def ensure_project_folders() -> None:
    folders = [
        DATA_DIR, KNOWN_FACES_DIR, MEETINGS_DIR, TRANSLATIONS_DIR, BACKUPS_DIR, EXPORTS_DIR,
        MODELS_DIR, OBJECT_MODELS_DIR, FACE_MODELS_DIR, EMOTION_MODELS_DIR, SPEECH_MODELS_DIR,
        IMAGES_DIR, CAPTURED_IMAGES_DIR, SAMPLES_DIR, UNKNOWN_IMAGES_DIR,
        SOUNDS_DIR, RECORDED_SOUNDS_DIR, OUTPUT_VOICE_DIR, LOGS_DIR, TESTS_DIR,
    ]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
    users_json = DATA_DIR / "users.json"
    if not users_json.exists():
        users_json.write_text("[]\n", encoding="utf-8")
    for name in ("system.log", "security.log", "meetings.log", "ai.log"):
        (LOGS_DIR / name).touch(exist_ok=True)
