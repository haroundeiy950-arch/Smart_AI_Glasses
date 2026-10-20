"""Ultralytics YOLO object detection with lazy model loading."""
from __future__ import annotations
from typing import Any
from camera_service import CameraService
from config import YOLO_CONFIDENCE,YOLO_MODEL
from privacy_manager import PrivacyManager

class ObjectDetector:
    def __init__(self,camera: CameraService,privacy: PrivacyManager): self.camera=camera; self.privacy=privacy; self.model: Any|None=None
    @property
    def available(self)->bool:
        try: import ultralytics; return True
        except ImportError: return False
    def load(self):
        if self.model is None:
            try: from ultralytics import YOLO
            except ImportError as exc: raise RuntimeError("Install ultralytics from requirements-ai.txt") from exc
            self.model=YOLO(YOLO_MODEL)
        return self.model
    def detect_frame(self,frame)->tuple[Any,list[dict[str,Any]]]:
        model=self.load(); results=model.predict(source=frame,conf=YOLO_CONFIDENCE,verbose=False); annotated=results[0].plot(); detections=[]
        names=results[0].names
        for box in results[0].boxes:
            cls_id=int(box.cls[0]); detections.append({"name":names.get(cls_id,str(cls_id)),"confidence":float(box.conf[0]),"box":[float(v) for v in box.xyxy[0].tolist()]})
        return annotated,detections
    def live(self):
        self.privacy.require("camera")
        try: import cv2
        except ImportError as exc: raise RuntimeError("Install opencv-contrib-python") from exc
        try:
            while True:
                frame=self.camera.read(); annotated,_=self.detect_frame(frame); cv2.putText(annotated,"Q/ESC: close",(20,35),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2); cv2.imshow("YOLO Object Detection",annotated)
                if cv2.waitKey(1)&0xFF in (27,ord('q')): break
        finally: self.camera.close(); cv2.destroyAllWindows()
