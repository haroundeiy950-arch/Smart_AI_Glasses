"""Optional emotion estimation. Results are approximate indicators only."""
from __future__ import annotations
from typing import Any
from camera_service import CameraService
from privacy_manager import PrivacyManager

class EmotionAnalyzer:
    def __init__(self,camera: CameraService,privacy: PrivacyManager): self.camera=camera; self.privacy=privacy
    @property
    def available(self)->bool:
        try: import deepface; return True
        except ImportError: return False
    def analyze_frame(self,frame)->dict[str,Any]:
        try: from deepface import DeepFace
        except ImportError as exc: raise RuntimeError("Install deepface from requirements-ai.txt") from exc
        result=DeepFace.analyze(img_path=frame,actions=['emotion'],enforce_detection=False,silent=True)
        if isinstance(result,list): result=result[0]
        return {"dominant_emotion":result.get('dominant_emotion','unknown'),"scores":result.get('emotion',{}),"warning":"Approximate indicator; not a medical or legal judgment."}
    @staticmethod
    def analyze_audio_tone(wav_path: str)->dict[str,Any]:
        """Estimate simple voice energy/pace signals from a PCM WAV file; not a true emotion diagnosis."""
        import wave
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Install numpy for audio tone analysis") from exc
        with wave.open(str(wav_path),'rb') as wf:
            channels=wf.getnchannels(); width=wf.getsampwidth(); rate=wf.getframerate(); raw=wf.readframes(wf.getnframes())
        dtype={1:np.int8,2:np.int16,4:np.int32}.get(width)
        if dtype is None: raise RuntimeError("Unsupported WAV sample width")
        samples=np.frombuffer(raw,dtype=dtype).astype('float32')
        if channels>1: samples=samples.reshape(-1,channels).mean(axis=1)
        if samples.size==0: return {"tone":"unknown","energy":0.0,"zero_crossing_rate":0.0,"warning":"No audio data"}
        peak=float(np.iinfo(dtype).max); normalized=samples/max(1.0,peak); energy=float(np.sqrt(np.mean(normalized**2))); zcr=float(np.mean(np.abs(np.diff(np.signbit(normalized)))))
        tone="energetic" if energy>0.12 else "calm" if energy<0.04 else "moderate"
        return {"tone":tone,"energy":round(energy,4),"zero_crossing_rate":round(zcr,4),"sample_rate":rate,"warning":"Acoustic indicator only; it does not determine a person's emotion."}

    @staticmethod
    def analyze_text_tone(text: str)->dict[str,Any]:
        lower=text.lower(); signals={"positive":["happy","great","thanks","سعيد","ممتاز","شكرا","neza","murakoze"],"negative":["sad","bad","angry","حزين","غاضب","سيء","mbi"],"urgent":["urgent","immediately","عاجل","فورا","byihutirwa"]}
        scores={k:sum(1 for word in words if word in lower) for k,words in signals.items()}; dominant=max(scores,key=scores.get) if any(scores.values()) else "neutral"
        return {"dominant_tone":dominant,"signals":scores,"warning":"Text tone is heuristic only."}
    def live(self):
        self.privacy.require("camera")
        try: import cv2
        except ImportError as exc: raise RuntimeError("Install opencv-contrib-python") from exc
        last="Press SPACE to analyze"
        try:
            while True:
                frame=self.camera.read(); cv2.putText(frame,last[:80],(20,35),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,255),2); cv2.putText(frame,"SPACE analyze | Q close",(20,70),cv2.FONT_HERSHEY_SIMPLEX,0.65,(255,255,255),2); cv2.imshow("Emotion Estimate",frame); key=cv2.waitKey(1)&0xFF
                if key in (27,ord('q')): break
                if key==32:
                    result=self.analyze_frame(frame); last=f"Estimated: {result['dominant_emotion']}"; print(result)
        finally: self.camera.close(); cv2.destroyAllWindows()
