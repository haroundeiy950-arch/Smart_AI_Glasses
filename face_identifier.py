"""Consent-based local face registration, LBPH training, recognition and face unlock."""
from __future__ import annotations
import json,re,shutil,time
from datetime import datetime
from pathlib import Path
from typing import Any
from camera_service import CameraService
from config import FACE_CASCADE_PATH,FACE_LABELS_PATH,FACE_MODEL_PATH,FACE_SAMPLE_COUNT,FACE_SIZE,FACE_UNKNOWN_THRESHOLD,KNOWN_FACES_DIR,UNKNOWN_CAPTURE_COOLDOWN_SECONDS,UNKNOWN_IMAGES_DIR
from database import DatabaseManager
from logger import get_logger
from privacy_manager import PrivacyManager
from security import SecurityManager

log=get_logger(__name__)

def safe_code(value: str)->str:
    value=re.sub(r"[^A-Za-z0-9_-]+","_",value.strip()).strip("_")
    if not value: raise ValueError("Person code must contain letters or numbers")
    return value

class FaceIdentifier:
    def __init__(self,camera: CameraService,database: DatabaseManager,privacy: PrivacyManager,security: SecurityManager):
        self.camera=camera; self.db=database; self.privacy=privacy; self.security=security
    @staticmethod
    def _cv2():
        try: import cv2; return cv2
        except ImportError as exc: raise RuntimeError("Install opencv-contrib-python") from exc
    def _cascade(self):
        cv2=self._cv2(); candidates=[FACE_CASCADE_PATH]
        if hasattr(cv2,"data"): candidates.append(Path(cv2.data.haarcascades)/"haarcascade_frontalface_default.xml")
        for path in candidates:
            if path.exists():
                cascade=cv2.CascadeClassifier(str(path))
                if not cascade.empty(): return cascade
        raise RuntimeError("Haar cascade not found. Reinstall opencv-contrib-python")
    def _recognizer(self):
        cv2=self._cv2()
        if not hasattr(cv2,"face") or not hasattr(cv2.face,"LBPHFaceRecognizer_create"):
            raise RuntimeError("cv2.face is missing. Remove opencv-python and install opencv-contrib-python")
        return cv2.face.LBPHFaceRecognizer_create()
    def register_person(self,person_code: str,name: str,job_title: str="",phone: str="",notes: str="",consent: bool=False,linked_user_id: int|None=None,sample_count: int=FACE_SAMPLE_COUNT)->dict[str,Any]:
        self.privacy.require("camera"); self.privacy.require("face_recognition")
        if not consent: raise PermissionError("Clear consent is required before saving face samples")
        cv2=self._cv2(); cascade=self._cascade(); code=safe_code(person_code); folder=KNOWN_FACES_DIR/code
        folder.mkdir(parents=True,exist_ok=True)
        count=0; last_saved=0.0
        try:
            while count<sample_count:
                frame=self.camera.read(); gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                faces=cascade.detectMultiScale(gray,scaleFactor=1.15,minNeighbors=5,minSize=(70,70))
                for x,y,w,h in faces[:1]:
                    cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                    if time.monotonic()-last_saved>=0.18:
                        face=cv2.resize(gray[y:y+h,x:x+w],FACE_SIZE)
                        count+=1; cv2.imwrite(str(folder/f"sample_{count:03d}.jpg"),face); last_saved=time.monotonic()
                cv2.putText(frame,f"Samples: {count}/{sample_count}",(20,35),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2)
                cv2.putText(frame,"Look forward and move your head slowly | Q cancel",(20,70),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),2)
                cv2.imshow("Register Person",frame)
                if cv2.waitKey(1)&0xFF in (27,ord('q')): break
        finally:
            self.camera.close(); cv2.destroyAllWindows()
        if count<5: raise RuntimeError(f"Only {count} samples captured; at least 5 are required")
        person_id=self.db.upsert_known_person(code,name.strip(),job_title.strip(),phone.strip(),notes.strip(),str(folder),True,linked_user_id)
        self.security.audit("FACE_REGISTERED",f"Registered {name} with {count} samples",user_id=linked_user_id,metadata={"person_id":person_id})
        return {"person_id":person_id,"samples":count,"folder":str(folder)}
    def train_model(self)->dict[str,Any]:
        cv2=self._cv2(); recognizer=self._recognizer(); faces=[]; labels=[]; label_map={}; next_label=0
        for person in self.db.list_known_people():
            folder=Path(person['folder_path'])
            samples=[]
            if folder.exists():
                for path in sorted(folder.glob("*.jpg")):
                    img=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
                    if img is not None: samples.append(cv2.resize(img,FACE_SIZE))
            if not samples: continue
            label_map[str(next_label)]={"person_id":int(person['id']),"person_code":person['person_code'],"name":person['name'],"linked_user_id":person.get('linked_user_id')}
            faces.extend(samples); labels.extend([next_label]*len(samples)); next_label+=1
        if not faces: raise RuntimeError("No valid face samples. Register a person first")
        try: import numpy as np
        except ImportError as exc: raise RuntimeError("Install numpy") from exc
        recognizer.train(faces,np.array(labels,dtype="int32")); FACE_MODEL_PATH.parent.mkdir(parents=True,exist_ok=True)
        recognizer.write(str(FACE_MODEL_PATH)); FACE_LABELS_PATH.write_text(json.dumps(label_map,ensure_ascii=False,indent=2),encoding="utf-8")
        self.security.audit("FACE_MODEL_TRAINED",f"Trained {len(label_map)} people from {len(faces)} samples")
        return {"people":len(label_map),"samples":len(faces),"model":str(FACE_MODEL_PATH)}
    def _load(self):
        if not FACE_MODEL_PATH.exists() or not FACE_LABELS_PATH.exists(): raise RuntimeError("Face model missing. Train the model first")
        recognizer=self._recognizer(); recognizer.read(str(FACE_MODEL_PATH)); labels=json.loads(FACE_LABELS_PATH.read_text(encoding="utf-8")); return recognizer,labels
    @staticmethod
    def match_score(distance: float)->float: return max(0.0,min(100.0,100.0-distance))
    def recognize_frame(self,frame)->list[dict[str,Any]]:
        self.privacy.require("face_recognition"); cv2=self._cv2(); cascade=self._cascade(); recognizer,labels=self._load()
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY); found=[]
        for x,y,w,h in cascade.detectMultiScale(gray,1.15,5,minSize=(70,70)):
            face=cv2.resize(gray[y:y+h,x:x+w],FACE_SIZE); label,distance=recognizer.predict(face); item=labels.get(str(label)) if distance<=FACE_UNKNOWN_THRESHOLD else None
            found.append({"box":(x,y,w,h),"known":item is not None,"distance":float(distance),"score":self.match_score(float(distance)),"person":item})
        return found
    def recognize_live(self)->None:
        self.privacy.require("camera"); self.privacy.require("face_recognition")
        cv2=self._cv2(); last_unknown=0.0
        try:
            while True:
                frame=self.camera.read(); results=self.recognize_frame(frame)
                for result in results:
                    x,y,w,h=result['box']; known=result['known']; color=(0,200,0) if known else (0,0,255)
                    label=f"{result['person']['name']} {result['score']:.0f}%" if known else "UNKNOWN"
                    cv2.rectangle(frame,(x,y),(x+w,y+h),color,2); cv2.putText(frame,label,(x,max(25,y-8)),cv2.FONT_HERSHEY_SIMPLEX,0.7,color,2)
                    if not known and self.privacy.get_permissions().get('save_unknown_faces') and time.monotonic()-last_unknown>=UNKNOWN_CAPTURE_COOLDOWN_SECONDS:
                        UNKNOWN_IMAGES_DIR.mkdir(parents=True,exist_ok=True); path=UNKNOWN_IMAGES_DIR/f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                        cv2.imwrite(str(path),frame[y:y+h,x:x+w]); self.db.add_unknown_event(str(path),result['score']); self.security.audit("UNKNOWN_FACE",f"Unknown face saved: {path}","WARNING"); last_unknown=time.monotonic()
                cv2.putText(frame,"Q/ESC: close",(20,35),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2); cv2.imshow("Live Face Recognition",frame)
                if cv2.waitKey(1)&0xFF in (27,ord('q')): break
        finally: self.camera.close(); cv2.destroyAllWindows()
    def verify_user_face(self,user_id: int,timeout_seconds: int=15)->dict[str,Any]|None:
        self.privacy.require("camera"); self.privacy.require("face_recognition"); cv2=self._cv2(); deadline=time.monotonic()+timeout_seconds; matched=None
        try:
            while time.monotonic()<deadline:
                frame=self.camera.read(); results=self.recognize_frame(frame)
                for r in results:
                    person=r.get('person')
                    if r['known'] and person and int(person.get('linked_user_id') or 0)==int(user_id): matched=person
                    x,y,w,h=r['box']; color=(0,200,0) if matched else (0,165,255); cv2.rectangle(frame,(x,y),(x+w,y+h),color,2)
                cv2.putText(frame,"Face Unlock - look at camera | Q cancel",(20,35),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2); cv2.imshow("Face Unlock",frame)
                if matched: cv2.waitKey(800); break
                if cv2.waitKey(1)&0xFF in (27,ord('q')): break
        finally: self.camera.close(); cv2.destroyAllWindows()
        return matched
    def list_people(self): return self.db.list_known_people()
    def delete_person(self,person_id: int):
        person=self.db.get_known_person(person_id)
        if not person: raise ValueError("Person not found")
        shutil.rmtree(person['folder_path'],ignore_errors=True); self.db.delete_known_person(person_id); self.security.audit("FACE_DELETED",f"Deleted {person['name']}")
    def link_to_user(self,person_id: int,user_id: int|None): self.db.link_person_to_user(person_id,user_id)
