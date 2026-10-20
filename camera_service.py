"""Camera lifecycle, probing, capture and preview."""
from __future__ import annotations
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from config import CAMERA_BACKEND,CAMERA_CANDIDATES,CAMERA_HEIGHT,CAMERA_INDEX,CAMERA_WIDTH,CAPTURED_IMAGES_DIR
from logger import get_logger
from privacy_manager import PrivacyManager

log=get_logger(__name__)

@dataclass(slots=True)
class CameraStatus:
    available: bool
    index: int|None
    message: str

class CameraService:
    def __init__(self,privacy: PrivacyManager):
        self.privacy=privacy; self.cap: Any|None=None; self.active_index: int|None=None
    @staticmethod
    def _cv2():
        try: import cv2; return cv2
        except ImportError as exc: raise RuntimeError("OpenCV missing. Install opencv-contrib-python") from exc
    def _backend(self,cv2):
        if CAMERA_BACKEND=="dshow" and hasattr(cv2,"CAP_DSHOW"): return cv2.CAP_DSHOW
        if CAMERA_BACKEND=="msmf" and hasattr(cv2,"CAP_MSMF"): return cv2.CAP_MSMF
        return None
    def open(self):
        self.privacy.require("camera")
        if self.cap is not None and self.cap.isOpened(): return self.cap
        cv2=self._cv2(); candidates=[]
        for idx in (CAMERA_INDEX,*CAMERA_CANDIDATES):
            if idx not in candidates: candidates.append(idx)
        backend=self._backend(cv2)
        for idx in candidates:
            cap=cv2.VideoCapture(idx,backend) if backend is not None else cv2.VideoCapture(idx)
            if not cap.isOpened(): cap.release(); continue
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,CAMERA_WIDTH); cap.set(cv2.CAP_PROP_FRAME_HEIGHT,CAMERA_HEIGHT)
            ok,frame=cap.read()
            if ok and frame is not None:
                self.cap=cap; self.active_index=idx; log.info("Camera opened at index %s",idx); return cap
            cap.release()
        raise RuntimeError("Camera not found. Close Camera/Zoom/Teams and try CAMERA_INDEX 0, 1, 2, or 3")
    def close(self):
        if self.cap is not None:
            try: self.cap.release()
            finally: self.cap=None; self.active_index=None
    def read(self):
        cap=self.open(); ok,frame=cap.read()
        if not ok or frame is None: raise RuntimeError("Camera opened but no frame was received")
        return frame
    def status(self)->CameraStatus:
        try:
            self.open(); frame=self.read(); return CameraStatus(frame is not None,self.active_index,f"Camera {self.active_index} is ready")
        except Exception as exc: return CameraStatus(False,None,str(exc))
        finally: self.close()
    def capture_image(self,prefix: str="capture")->Path:
        cv2=self._cv2(); frame=self.read(); CAPTURED_IMAGES_DIR.mkdir(parents=True,exist_ok=True)
        path=CAPTURED_IMAGES_DIR/f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        if not cv2.imwrite(str(path),frame): raise RuntimeError("Could not save captured image")
        log.info("Captured image: %s",path); return path
    def preview(self,title: str="Smart AI Glasses Camera",seconds: int|None=None):
        cv2=self._cv2(); started=time.monotonic()
        try:
            while True:
                frame=self.read(); cv2.putText(frame,"Q/ESC: close | C: capture",(20,35),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2)
                cv2.imshow(title,frame); key=cv2.waitKey(1)&0xFF
                if key in (27,ord('q')): break
                if key==ord('c'): self.capture_image("manual")
                if seconds and time.monotonic()-started>=seconds: break
        finally:
            self.close(); cv2.destroyAllWindows()
