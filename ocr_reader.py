"""Tesseract OCR for images and live camera."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from camera_service import CameraService
from config import OCR_LANGUAGES,TESSERACT_CMD
from privacy_manager import PrivacyManager

class OCRReader:
    def __init__(self,camera: CameraService,privacy: PrivacyManager): self.camera=camera; self.privacy=privacy
    @staticmethod
    def _pytesseract():
        try: import pytesseract
        except ImportError as exc: raise RuntimeError("Install pytesseract and Tesseract OCR desktop program") from exc
        if TESSERACT_CMD: pytesseract.pytesseract.tesseract_cmd=TESSERACT_CMD
        return pytesseract
    def read_image(self,image: str|Path|Any,languages: str=OCR_LANGUAGES)->str:
        pytesseract=self._pytesseract()
        try: import cv2
        except ImportError as exc: raise RuntimeError("Install opencv-contrib-python") from exc
        frame=cv2.imread(str(image)) if isinstance(image,(str,Path)) else image
        if frame is None: raise ValueError("Image could not be loaded")
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY); gray=cv2.GaussianBlur(gray,(3,3),0); processed=cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
        return pytesseract.image_to_string(processed,lang=languages).strip()
    def capture_and_read(self)->tuple[Path,str]:
        path=self.camera.capture_image("ocr"); return path,self.read_image(path)
    def live(self):
        self.privacy.require("camera")
        try: import cv2
        except ImportError as exc: raise RuntimeError("Install opencv-contrib-python") from exc
        last_text=""
        try:
            while True:
                frame=self.camera.read(); display=frame.copy(); cv2.putText(display,"SPACE: read | Q: close",(20,35),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2)
                if last_text: cv2.putText(display,last_text[:80],(20,70),cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,255,255),2)
                cv2.imshow("Live OCR",display); key=cv2.waitKey(1)&0xFF
                if key in (27,ord('q')): break
                if key==32: last_text=self.read_image(frame) or "No text found"; print(last_text)
        finally: self.camera.close(); cv2.destroyAllWindows()
