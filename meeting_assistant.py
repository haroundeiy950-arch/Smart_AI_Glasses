"""Meeting capture, translation, summarization, decisions, tasks, export and history."""
from __future__ import annotations
import json,re
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from ai_service import AIService
from audio_recorder import AudioRecorder
from config import EXPORTS_DIR,MEETINGS_DIR
from database import DatabaseManager
from logger import get_logger
from privacy_manager import PrivacyManager
from speech_to_text import SpeechToText
from translator_service import TranslatorService

log=get_logger("meetings")

def utc_now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")

LANGUAGE_SPEECH_CODES={'ar':'ar-SA','en':'en-US','fr':'fr-FR','rw':'rw-RW','sw':'sw-KE','es':'es-ES','de':'de-DE','pt':'pt-PT','it':'it-IT','tr':'tr-TR','zh-CN':'zh-CN','hi':'hi-IN'}

@dataclass(slots=True)
class MeetingResult:
    meeting_id: int
    title: str
    summary: str
    decisions: list[str]
    tasks: list[str]
    translated_transcript: str
    audio_path: str|None

class MeetingAssistant:
    TASK_MARKERS=("todo","task","action","must","should","need to","responsible","مهمة","يجب","مطلوب","مسؤول","لازم","gomba","inshingano")
    DECISION_MARKERS=("decided","decision","agreed","approved","قرار","اتفقنا","تمت الموافقة","twemeje","icyemezo")
    def __init__(self,database: DatabaseManager,translator: TranslatorService,ai_service: AIService,privacy: PrivacyManager,speech: SpeechToText,audio: AudioRecorder):
        self.db=database; self.translator=translator; self.ai=ai_service; self.privacy=privacy; self.speech=speech; self.audio=audio
        self.session: dict[str,Any]|None=None
    @staticmethod
    def _sentences(text: str)->list[str]: return [s.strip() for s in re.split(r"(?<=[.!?؟])\s+|\n+",text) if s.strip()]
    def heuristic_summary(self,text: str,max_sentences: int=6)->str:
        sentences=self._sentences(text)
        if not sentences: return "No transcript was provided."
        important=[s for s in sentences if any(k in s.lower() for k in ("important","decision","agree","result","مهم","قرار","اتفق","نتيجة","ingenzi","icyemezo"))]
        selected=(important+[s for s in sentences if s not in important])[:max_sentences]
        return "\n".join(f"• {s}" for s in selected)
    def extract_tasks(self,text: str)->list[str]: return [s for s in self._sentences(text) if any(k in s.lower() for k in self.TASK_MARKERS)][:30]
    def extract_decisions(self,text: str)->list[str]: return [s for s in self._sentences(text) if any(k in s.lower() for k in self.DECISION_MARKERS)][:30]
    def summarize(self,text: str,use_ai: bool,user_id: int|None)->tuple[str,list[str],list[str]]:
        tasks=self.extract_tasks(text); decisions=self.extract_decisions(text)
        if use_ai and text.strip():
            answer=self.ai.ask("Summarize this meeting in bullet points. Then list decisions and action items. Do not invent facts.\n\n"+text[:16000],context_type="meeting",user_id=user_id)
            if answer.provider.startswith("openai/"): return answer.answer,tasks,decisions
        return self.heuristic_summary(text),tasks,decisions
    def start_session(self,title: str,participants: list[str],source_language: str,target_language: str,consent: bool,record_audio: bool=False)->dict[str,Any]:
        if not consent: raise PermissionError("Participant consent must be confirmed")
        self.privacy.require("meeting_recording")
        if self.session: raise RuntimeError("A meeting session is already active")
        audio_path=None
        if record_audio: audio_path=str(self.audio.start())
        self.session={"title":title.strip() or "Untitled Meeting","participants":participants,"source_language":source_language,"target_language":target_language,"consent":True,"started_at":utc_now(),"utterances":[],"audio_path":audio_path}
        return dict(self.session)
    def add_utterance(self,text: str,speaker: str="",language: str="",user_id: int|None=None)->dict[str,str]:
        if not self.session: raise RuntimeError("Start a meeting first")
        if not text.strip(): return {"text":"","translation":""}
        source=language or self.session['source_language']; translation=""
        if self.session['target_language'] and self.session['target_language']!=source:
            try: translation=self.translator.translate(text.strip(),source,self.session['target_language'],user_id).translated_text
            except Exception as exc: translation=f"[Translation unavailable: {exc}]"
        item={"speaker":speaker.strip() or "Speaker","text":text.strip(),"translation":translation,"language":source,"time":utc_now()}; self.session['utterances'].append(item); return {"text":item['text'],"translation":translation}
    def listen_utterance(self,speaker: str="",speech_language: str="en-US",user_id: int|None=None)->dict[str,str]:
        text=self.speech.listen_once(speech_language); return self.add_utterance(text,speaker,self.session['source_language'] if self.session else speech_language,user_id)
    def finish_session(self,use_ai: bool=True,user_id: int|None=None,translate_transcript: bool=True)->MeetingResult:
        if not self.session: raise RuntimeError("No active meeting")
        session=self.session; audio_path=session.get('audio_path')
        if self.audio.recording: audio_path=str(self.audio.stop())
        transcript="\n".join(f"[{u['speaker']}] {u['text']}" + (f"\n  → {u.get('translation','')}" if u.get('translation') else "") for u in session['utterances'])
        if not transcript.strip() and audio_path:
            try: transcript=self.speech.transcribe_wav(audio_path,LANGUAGE_SPEECH_CODES.get(session['source_language'],'en-US'))
            except Exception: pass
        result=self.save_meeting(session['title'],session['participants'],transcript,session['source_language'],session['target_language'],True,use_ai,user_id,audio_path,session['started_at'],translate_transcript)
        self.session=None; return result
    def save_meeting(self,title: str,participants: list[str],transcript: str,source_language: str,target_language: str,consent_confirmed: bool,use_ai: bool=True,user_id: int|None=None,audio_path: str|None=None,started_at: str|None=None,translate_transcript: bool=True)->MeetingResult:
        if not title.strip(): raise ValueError("Meeting title is required")
        if not consent_confirmed: raise PermissionError("Confirm participant consent before saving")
        self.privacy.require("meeting_recording")
        translated=""
        if translate_transcript and transcript.strip() and target_language and target_language!=source_language:
            try: translated=self.translator.translate(transcript,source_language,target_language,user_id).translated_text
            except Exception as exc: translated=f"[Translation unavailable: {exc}]"
        summary,tasks,decisions=self.summarize(transcript,use_ai,user_id)
        meeting_id=self.db.create_meeting(title.strip(),participants,source_language,target_language,transcript.strip(),translated,summary,decisions,tasks,audio_path,True,user_id,started_at,utc_now())
        payload={"id":meeting_id,"title":title.strip(),"participants":participants,"transcript":transcript,"translated_transcript":translated,"summary":summary,"decisions":decisions,"tasks":tasks,"audio_path":audio_path}
        MEETINGS_DIR.mkdir(parents=True,exist_ok=True); (MEETINGS_DIR/f"meeting_{meeting_id}.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
        log.info("Meeting saved: %s",meeting_id); return MeetingResult(meeting_id,title.strip(),summary,decisions,tasks,translated,audio_path)
    def list_meetings(self): return self.db.list_meetings()
    def get_meeting(self,meeting_id: int): return self.db.get_meeting(meeting_id)
    def delete_meeting(self,meeting_id: int): self.db.delete_meeting(meeting_id)
    def export_meeting(self,meeting_id: int,fmt: str="txt")->Path:
        row=self.db.get_meeting(meeting_id)
        if not row: raise ValueError("Meeting not found")
        EXPORTS_DIR.mkdir(parents=True,exist_ok=True); fmt=fmt.lower(); path=EXPORTS_DIR/f"meeting_{meeting_id}.{fmt}"
        if fmt=="json": path.write_text(json.dumps(row,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        else:
            text=f"Title: {row['title']}\nParticipants: {row.get('participants','')}\nStarted: {row.get('started_at','')}\n\nTRANSCRIPT\n{row.get('transcript','')}\n\nTRANSLATION\n{row.get('translated_transcript','')}\n\nSUMMARY\n{row.get('summary','')}\n\nDECISIONS\n{row.get('decisions','')}\n\nTASKS\n{row.get('tasks','')}\n"
            path.write_text(text,encoding="utf-8")
        return path
