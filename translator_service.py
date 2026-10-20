"""Text translation with Kinyarwanda support and a small offline emergency phrasebook."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from config import LANGUAGES
from database import DatabaseManager

@dataclass(slots=True)
class TranslationResult:
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    provider: str

class TranslatorService:
    PHRASES={
        ("en","rw","hello"):"Muraho",("en","rw","good morning"):"Mwaramutse",("en","rw","thank you"):"Murakoze",("en","rw","how are you?"):"Amakuru?",
        ("rw","en","muraho"):"Hello",("rw","en","mwaramutse"):"Good morning",("rw","en","murakoze"):"Thank you",("rw","en","amakuru?"):"How are you?",
        ("ar","rw","hello"):"Muraho",("ar","rw","Good morning"):"Mwaramutse",("ar","rw","think you"):"Murakoze",
        ("rw","ar","muraho"):"hello",("rw","ar","mwaramutse"):"Good morning",("rw","ar","murakoze"):"thinks",
    }
    def __init__(self,database: DatabaseManager): self.db=database
    def supported_languages(self): return LANGUAGES
    def translate(self,text: str,source_language: str="auto",target_language: str="rw",user_id: int|None=None)->TranslationResult:
        text=text.strip()
        if not text: raise ValueError("Enter text to translate")
        if target_language not in LANGUAGES or target_language=="auto": raise ValueError("Unsupported target language")
        if source_language not in LANGUAGES: raise ValueError("Unsupported source language")
        key=(source_language,target_language,text.lower())
        translated=self.PHRASES.get(key); provider="offline-phrasebook" if translated else ""
        if translated is None:
            try:
                from deep_translator import GoogleTranslator
                src=source_language if source_language!="auto" else "auto"; translated=GoogleTranslator(source=src,target=target_language).translate(text); provider="googletranslator"
            except Exception as exc:
                if source_language==target_language: translated=text; provider="same-language"
                else: raise RuntimeError(f"Translation needs internet or a supported offline phrase. Details: {exc}") from exc
        self.db.add_translation(text,translated,source_language,target_language,provider,user_id)
        return TranslationResult(text,translated,source_language,target_language,provider)
