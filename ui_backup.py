"""Professional Tkinter control panel for Smart AI Glasses System."""
from __future__ import annotations

import json,threading,tkinter as tk
from pathlib import Path
from tkinter import filedialog,messagebox,simpledialog,ttk
from typing import Any,Callable

from config import DEFAULT_UI_LANGUAGE,FACE_MODEL_PATH,FACE_SAMPLE_COUNT,LANGUAGES,PROJECT_NAME,PROJECT_VERSION
from control_system import SystemController
from hud_display import HUDDisplay
from i18n import tr
from logger import get_logger

log=get_logger(__name__)

class LoginWindow:
    def __init__(self,controller: SystemController):
        self.controller=controller; self.root=tk.Tk(); self.root.title(f"{PROJECT_NAME} - Login"); self.root.geometry("560x500"); self.root.resizable(False,False); self.root.configure(bg="#0f172a")
        self.username=tk.StringVar(value="admin"); self.password=tk.StringVar(); self.language=tk.StringVar(value=DEFAULT_UI_LANGUAGE if DEFAULT_UI_LANGUAGE in {"ar","en","fr","rw"} else "ar"); self.main_app=None; self._build()
    def _build(self):
        card=tk.Frame(self.root,bg="white",padx=36,pady=30); card.place(relx=.5,rely=.5,anchor="center",width=470,height=420)
        tk.Label(card,text="SMART AI GLASSES",bg="white",fg="#0f172a",font=("Segoe UI",22,"bold")).pack()
        tk.Label(card,text=f"Integrated Control System v{PROJECT_VERSION}",bg="white",fg="#64748b").pack(pady=(3,22))
        tk.Label(card,text="Username / اسم المستخدم",bg="white",anchor="w").pack(fill="x"); ttk.Entry(card,textvariable=self.username,font=("Segoe UI",12)).pack(fill="x",pady=(4,12),ipady=6)
        tk.Label(card,text="Password / كلمة المرور",bg="white",anchor="w").pack(fill="x"); ttk.Entry(card,textvariable=self.password,show="●",font=("Segoe UI",12)).pack(fill="x",pady=(4,12),ipady=6)
        row=tk.Frame(card,bg="white"); row.pack(fill="x",pady=(0,14)); tk.Label(row,text="Interface:",bg="white").pack(side="left"); ttk.Combobox(row,textvariable=self.language,state="readonly",values=("ar","en","fr","rw"),width=12).pack(side="right")
        tk.Button(card,text="Login / تسجيل الدخول",command=self.login,bg="#2563eb",fg="white",relief="flat",font=("Segoe UI",11,"bold"),pady=10).pack(fill="x")
        tk.Button(card,text="Face Unlock / فتح بالوجه",command=self.face_login,bg="#059669",fg="white",relief="flat",font=("Segoe UI",10,"bold"),pady=9).pack(fill="x",pady=(8,0))
        tk.Label(card,text="Default login: admin / Haroun@123",bg="white",fg="#b45309").pack(pady=(12,0)); self.root.bind('<Return>',lambda _e:self.login())
    def _open(self,result):
        if not result.success:
            messagebox.showerror("Login failed",result.message,parent=self.root)
            return
        self.root.withdraw()
        try:
            self.main_app=SmartGlassesUI(self.controller,self.root,self.language.get())
        except Exception as exc:
            log.exception("Main interface could not start")
            self.root.deiconify()
            messagebox.showerror(
                "Interface error / خطأ في الواجهة",
                f"{type(exc).__name__}: {exc}\n\nراجع الملف logs/system.log",
                parent=self.root,
            )
    def login(self): self._open(self.controller.login(self.username.get(),self.password.get()))
    def face_login(self):
        username=self.username.get().strip()
        if not username: messagebox.showwarning("Username","Enter username first",parent=self.root); return
        def worker():
            try: result=self.controller.face_login(username); self.root.after(0,lambda:self._open(result))
            except Exception as exc: self.root.after(0,lambda:messagebox.showerror("Face Unlock",str(exc),parent=self.root))
        threading.Thread(target=worker,daemon=True).start()
    def run(self): self.root.mainloop()

class SmartGlassesUI:
    def __init__(self,controller: SystemController,login_root: tk.Tk,language: str="ar"):
        self.controller=controller; self.login_root=login_root; self.language=language
        self.root=tk.Toplevel(login_root)
        try:
            self.root.title(PROJECT_NAME)
            self.root.geometry("1380x860")
            self.root.minsize(1120,700)
            self.root.protocol("WM_DELETE_WINDOW",self.exit_application)
            self.status_var=tk.StringVar(value=tr("ready",language))
            self.hud=HUDDisplay(self.root)
            self._style()
            self._build_shell()
            # Let Tkinter paint the window first. Loading data during construction can
            # leave a blank white window when a database/path error occurs.
            self.root.after(250,self.refresh_all)
        except Exception:
            try:
                self.root.destroy()
            except Exception:
                pass
            raise
    def _style(self):
        style=ttk.Style(self.root)
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("TNotebook.Tab",font=("Segoe UI",10,"bold"),padding=(14,8)); style.configure("Treeview",rowheight=28,font=("Segoe UI",9)); style.configure("Treeview.Heading",font=("Segoe UI",9,"bold")); style.configure("Accent.TButton",font=("Segoe UI",10,"bold"))
    @staticmethod
    def section(parent,title): return ttk.LabelFrame(parent,text=title,padding=10)
    def _build_shell(self):
        header=tk.Frame(self.root,bg="#0f172a",height=70); header.pack(fill="x"); user=self.controller.current_user or {}
        tk.Label(header,text=PROJECT_NAME,bg="#0f172a",fg="white",font=("Segoe UI",18,"bold")).pack(side="left",padx=20,pady=18)
        tk.Label(header,text=f"{user.get('full_name','')} | {user.get('role','')}",bg="#0f172a",fg="#cbd5e1").pack(side="right",padx=(8,20)); tk.Button(header,text=tr("logout",self.language),command=self.logout,bg="#dc2626",fg="white",relief="flat",padx=14,pady=7).pack(side="right")
        tk.Button(header,text="HUD",command=lambda:self.hud.show("Smart AI Glasses ready"),bg="#0891b2",fg="white",relief="flat",padx=14,pady=7).pack(side="right",padx=8)
        self.notebook=ttk.Notebook(self.root); self.notebook.pack(fill="both",expand=True,padx=10,pady=10)
        self.tabs={key:ttk.Frame(self.notebook,padding=12) for key in ("dashboard","vision","translation","meetings","ask_ai","security","data_control","settings")}
        for key,frame in self.tabs.items(): self.notebook.add(frame,text=tr(key,self.language))
        self._build_dashboard(); self._build_vision(); self._build_translation(); self._build_meetings(); self._build_ai(); self._build_security(); self._build_data_control(); self._build_settings()
        tk.Label(self.root,textvariable=self.status_var,anchor="w",bg="#e2e8f0",fg="#0f172a",padx=12,pady=6).pack(fill="x",side="bottom")
    def run_task(self,label: str,function: Callable[[],Any],success: Callable[[Any],None]|None=None):
        self.status_var.set(label)
        def worker():
            try: result=function(); self.root.after(0,lambda:self._task_success(label,result,success))
            except Exception as exc: log.exception("Task failed"); self.root.after(0,lambda:self._task_error(label,exc))
        threading.Thread(target=worker,daemon=True).start()
    def _task_success(self,label,result,callback): self.status_var.set(f"Completed: {label}"); callback(result) if callback else None
    def _task_error(self,label,exc): self.status_var.set(f"Error: {exc}"); messagebox.showerror(label,str(exc),parent=self.root)
    def text_dialog(self,title,text):
        win=tk.Toplevel(self.root); win.title(title); win.geometry("850x580"); w=tk.Text(win,wrap="word",font=("Segoe UI",11)); w.insert("1.0",text); w.pack(fill="both",expand=True,padx=10,pady=10); ttk.Button(win,text="Close",command=win.destroy).pack(pady=(0,10))

    # dashboard
    def _build_dashboard(self):
        """Build a clean dashboard without counters, health tables, or notifications."""
        tab = self.tabs["dashboard"]

        top = ttk.Frame(tab)
        top.pack(fill="x", pady=(0, 16))

        user = self.controller.current_user or {}
        full_name = user.get("full_name", "User")

        ttk.Label(
            top,
            text=f"Welcome, {full_name}",
            font=("Segoe UI", 20, "bold"),
        ).pack(side="left")

        ttk.Button(
            top,
            text=tr("refresh", self.language),
            command=self.refresh_dashboard,
        ).pack(side="right")

        welcome = tk.Frame(
            tab,
            bg="#f8fafc",
            highlightbackground="#cbd5e1",
            highlightthickness=1,
            padx=30,
            pady=30,
        )
        welcome.pack(fill="both", expand=True)

        tk.Label(
            welcome,
            text="Smart AI Glasses System",
            bg="#f8fafc",
            fg="#0f172a",
            font=("Segoe UI", 28, "bold"),
        ).pack(pady=(90, 12))

        tk.Label(
            welcome,
            text=(
                "اختر القسم المطلوب من الأعلى لتشغيل الرؤية والكاميرا، "
                "الترجمة، الاجتماعات، Ask AI، الأمان، إدارة البيانات أو الإعدادات."
            ),
            bg="#f8fafc",
            fg="#475569",
            font=("Segoe UI", 13),
            justify="center",
            wraplength=900,
        ).pack(pady=(0, 24))

        quick = ttk.Frame(welcome)
        quick.pack()

        quick_actions = (
            (
                "Camera Preview",
                lambda: self.run_task(
                    "Camera preview",
                    self.controller.camera.preview,
                ),
            ),
            ("Face Recognition", self.start_live_face_recognition),
            (
                "Translation",
                lambda: self.notebook.select(self.tabs["translation"]),
            ),
            (
                "Ask AI",
                lambda: self.notebook.select(self.tabs["ask_ai"]),
            ),
        )

        for index, (label, command) in enumerate(quick_actions):
            ttk.Button(
                quick,
                text=label,
                command=command,
                style="Accent.TButton",
            ).grid(
                row=0,
                column=index,
                padx=6,
                pady=6,
                ipadx=10,
                ipady=5,
            )

    def refresh_dashboard(self):
        """Refresh only the clean dashboard status."""
        self.status_var.set("Dashboard ready")

    def refresh_health(self, quick=True):
        """Keep health checking available without showing it on the dashboard."""
        self.run_task(
            "System health",
            lambda: self.controller.health_check(quick),
            self.show_health,
        )

    def show_health(self, data):
        lines = []
        for component, info in data.items():
            lines.append(
                f"{component}: {info.get('status', '')}\n"
                f"{info.get('message', '')}"
            )
        self.text_dialog("System Health", "\n\n".join(lines))

    def mark_notification(self):
        # Notifications were intentionally removed from the dashboard UI.
        self.status_var.set("Notifications are hidden from the dashboard")

    # vision
    def _build_vision(self):
        tab=self.tabs['vision']; actions=self.section(tab,"Camera and AI Vision"); actions.pack(fill="x")
        buttons=[("Camera Preview",lambda:self.run_task("Camera preview",self.controller.camera.preview)),("Capture Image",self.capture_image),("Register Person",self.register_person),("Train Face Model",self.train_face),("Live Face Recognition",self.start_live_face_recognition),("YOLO Object Detection",lambda:self.run_task("Object detection",self.controller.object_detector.live)),("Capture OCR",self.capture_ocr),("Live OCR",lambda:self.run_task("Live OCR",self.controller.ocr.live)),("Emotion Estimate",lambda:self.run_task("Emotion",self.controller.emotion.live))]
        for i,(label,cmd) in enumerate(buttons): ttk.Button(actions,text=label,command=cmd,style="Accent.TButton").grid(row=i//3,column=i%3,sticky="ew",padx=5,pady=5)
        [actions.columnconfigure(i,weight=1) for i in range(3)]

        workflow=self.section(tab,"Face Recognition Setup Progress / خطوات إعداد التعرف على الوجه")
        workflow.pack(fill="x",pady=(10,0))
        self.face_workflow_var=tk.StringVar(value="")
        tk.Label(
            workflow,
            textvariable=self.face_workflow_var,
            justify="left",
            anchor="w",
            bg="#f8fafc",
            fg="#0f172a",
            font=("Segoe UI",11,"bold"),
            padx=14,
            pady=8,
        ).pack(fill="x")
        ttk.Button(workflow,text="Refresh Progress / تحديث الخطوات",command=self.update_face_workflow).pack(anchor="e",pady=(5,0))
        # Update after the complete Vision tab has been created.
        self.root.after(350,self.update_face_workflow)

        panes=ttk.Panedwindow(tab,orient="horizontal"); panes.pack(fill="both",expand=True,pady=(12,0)); people=self.section(panes,"Known People"); unknown=self.section(panes,"Unknown Events"); panes.add(people,weight=3); panes.add(unknown,weight=2)
        bar=ttk.Frame(people); bar.pack(fill="x"); ttk.Button(bar,text="Refresh",command=self.refresh_people).pack(side="left"); ttk.Button(bar,text="Delete",command=self.delete_person).pack(side="left",padx=5); ttk.Button(bar,text="Link to Current User",command=self.link_person).pack(side="left")
        self.people_tree=ttk.Treeview(people,columns=("id","code","name","job","phone","linked","samples"),show="headings"); widths=(50,100,150,130,110,70,260)
        for c,w in zip(("id","code","name","job","phone","linked","samples"),widths): self.people_tree.heading(c,text=c.title()); self.people_tree.column(c,width=w)
        self.people_tree.pack(fill="both",expand=True,pady=7)
        ub=ttk.Frame(unknown); ub.pack(fill="x"); ttk.Button(ub,text="Refresh",command=self.refresh_unknown).pack(side="left"); ttk.Button(ub,text="Review",command=self.review_unknown).pack(side="left",padx=5); ttk.Button(ub,text="Delete",command=self.delete_unknown).pack(side="left")
        self.unknown_tree=ttk.Treeview(unknown,columns=("id","time","score","reviewed","path"),show="headings");
        for c,w in (("id",45),("time",150),("score",60),("reviewed",70),("path",260)): self.unknown_tree.heading(c,text=c.title()); self.unknown_tree.column(c,width=w)
        self.unknown_tree.pack(fill="both",expand=True,pady=7)
    def capture_image(self): self.run_task("Capture image",self.controller.camera.capture_image,lambda p:messagebox.showinfo("Captured",str(p),parent=self.root))

    def _face_setup_state(self)->dict[str,Any]:
        """Return face setup statistics without crashing the whole interface."""
        try:
            people=self.controller.face_identifier.list_people() or []
        except Exception:
            log.exception("Could not load known people for face workflow")
            people=[]

        total_samples=0
        for person in people:
            try:
                folder_value=person.get("folder_path") if isinstance(person,dict) else person["folder_path"]
                if not folder_value:
                    continue
                folder=Path(str(folder_value))
                if folder.exists() and folder.is_dir():
                    total_samples+=sum(
                        1 for path in folder.iterdir()
                        if path.is_file() and path.suffix.lower() in {".jpg",".jpeg",".png"}
                    )
            except Exception:
                log.exception("Could not count samples for one known person")

        try:
            model_ready=Path(str(FACE_MODEL_PATH)).exists()
        except Exception:
            model_ready=False

        return {
            "people":len(people),
            "samples":total_samples,
            "model_ready":model_ready,
        }

    def _face_workflow_text(self,current: str|None=None)->str:
        state=self._face_setup_state()
        registered=state["people"]>0
        samples_ready=state["samples"]>=5
        model_ready=bool(state["model_ready"])
        if current is None:
            if not registered: current="register"
            elif not samples_ready: current="register"
            elif not model_ready: current="train"
            else: current="live"
        def line(label: str,key: str,done: bool,details: str="")->str:
            if done: marker="✅"
            elif current==key: marker="← الخطوة الحالية"
            else: marker="⏳"
            suffix=f" ({details})" if details else ""
            return f"{label}{suffix} {marker}"
        sample_label=f"{FACE_SAMPLE_COUNT} Face Samples"
        if state["samples"] and state["samples"]!=FACE_SAMPLE_COUNT:
            sample_label=f"Face Samples: {state['samples']}/{FACE_SAMPLE_COUNT}"
        return "\n".join([
            line("Register Person","register",registered,f"{state['people']} person(s)" if registered else ""),
            line(sample_label,"register",samples_ready),
            line("Train Face Model","train",model_ready),
            line("Live Face Recognition","live",False if current=="live" else model_ready),
        ])

    def update_face_workflow(self,current: str|None=None):
        if not hasattr(self,"face_workflow_var"):
            return
        try:
            self.face_workflow_var.set(self._face_workflow_text(current))
        except Exception as exc:
            log.exception("Could not update face recognition progress")
            self.face_workflow_var.set(
                "تعذر قراءة خطوات التعرف على الوجه.\n"
                f"الخطأ: {type(exc).__name__}: {exc}\n"
                "راجع logs/system.log"
            )

    def _show_face_workflow(self,title: str,current: str|None=None,extra: str=""):
        text=self._face_workflow_text(current)
        if extra: text=f"{text}\n\n{extra}"
        self.update_face_workflow(current)
        messagebox.showinfo(title,text,parent=self.root)

    def register_person(self):
        code=simpledialog.askstring("Code","Unique person code:",parent=self.root); name=simpledialog.askstring("Name","Full name:",parent=self.root) if code else None
        if not code or not name: return
        job=simpledialog.askstring("Job","Job or relationship:",parent=self.root) or ""; phone=simpledialog.askstring("Phone","Phone (optional):",parent=self.root) or ""; notes=simpledialog.askstring("Notes","Notes:",parent=self.root) or ""; consent=messagebox.askyesno("Consent","Did the person clearly consent?",parent=self.root)
        if not consent: return
        self.run_task(
            "Registering person",
            lambda:self.controller.face_identifier.register_person(code,name,job,phone,notes,True),
            lambda r:(
                self.refresh_people(),
                self._show_face_workflow(
                    "Registration completed / اكتمل التسجيل",
                    "train",
                    f"Captured face samples: {r['samples']}\nNext: press Train Face Model.",
                ),
            ),
        )

    def train_face(self):
        self.run_task(
            "Train face model",
            self.controller.face_identifier.train_model,
            lambda r:self._show_face_workflow(
                "Training completed / اكتمل التدريب",
                "live",
                f"People trained: {r['people']}\nSamples used: {r['samples']}\nModel saved successfully.\n\nاضغط الآن Live Face Recognition.",
            ),
        )

    def start_live_face_recognition(self):
        self.update_face_workflow("live")
        self.run_task(
            "Face recognition",
            self.controller.face_identifier.recognize_live,
            lambda _r:self.update_face_workflow("live"),
        )
    def refresh_people(self):
        rows=self.controller.face_identifier.list_people(); self.people_tree.delete(*self.people_tree.get_children())
        for r in rows: self.people_tree.insert('', 'end',values=(r['id'],r['person_code'],r['name'],r.get('job_title') or '',r.get('phone') or '',r.get('linked_user_id') or '',r['folder_path']))
    def _selected(self,tree):
        sel=tree.selection(); return tree.item(sel[0],'values') if sel else None
    def delete_person(self):
        v=self._selected(self.people_tree)
        if v and messagebox.askyesno("Delete",f"Delete {v[2]} and samples?",parent=self.root): self.controller.face_identifier.delete_person(int(v[0])); self.refresh_people()
    def link_person(self):
        v=self._selected(self.people_tree)
        if not v: messagebox.showwarning("Select","Select a person",parent=self.root); return
        self.controller.face_identifier.link_to_user(int(v[0]),self.controller.user_id); messagebox.showinfo("Linked","This face is now linked to your login account",parent=self.root); self.refresh_people()
    def refresh_unknown(self):
        self.unknown_tree.delete(*self.unknown_tree.get_children())
        for r in self.controller.database.list_unknown_events(): self.unknown_tree.insert('', 'end',values=(r['id'],r['created_at'],r.get('match_score'),"Yes" if r.get('reviewed') else "No",r.get('image_path') or ''))
    def review_unknown(self):
        v=self._selected(self.unknown_tree)
        if v: notes=simpledialog.askstring("Review","Review notes:",parent=self.root) or ""; self.controller.database.review_unknown_event(int(v[0]),notes); self.refresh_unknown()
    def delete_unknown(self):
        v=self._selected(self.unknown_tree)
        if v and messagebox.askyesno("Delete","Delete event and image?",parent=self.root):
            path=Path(v[4]); self.controller.database.delete_unknown_event(int(v[0])); path.unlink(missing_ok=True); self.refresh_unknown()
    def capture_ocr(self): self.run_task("OCR",self.controller.ocr.capture_and_read,lambda r:self.text_dialog("OCR Result",f"Image: {r[0]}\n\n{r[1] or 'No text found'}"))

    # translation
    def _build_translation(self):
        tab=self.tabs['translation']; values=[f"{c} — {info.get(self.language,info['en'])}" for c,info in LANGUAGES.items()]; self.source_lang=tk.StringVar(value=values[0]); self.target_lang=tk.StringVar(value=next(v for v in values if v.startswith('rw ')))
        controls=ttk.Frame(tab); controls.pack(fill="x"); ttk.Label(controls,text="Source").pack(side="left"); ttk.Combobox(controls,textvariable=self.source_lang,values=values,state="readonly",width=28).pack(side="left",padx=5); ttk.Label(controls,text="Target").pack(side="left",padx=(15,0)); ttk.Combobox(controls,textvariable=self.target_lang,values=[v for v in values if not v.startswith('auto ')],state="readonly",width=28).pack(side="left",padx=5)
        self.translation_input=tk.Text(self.section(tab,"Input text"),height=7,wrap="word",font=("Segoe UI",12)); self.translation_input.master.pack(fill="both",expand=True,pady=(10,5)); self.translation_input.pack(fill="both",expand=True)
        bar=ttk.Frame(tab); bar.pack(fill="x"); ttk.Button(bar,text="Translate",command=self.translate_text).pack(side="left"); ttk.Button(bar,text="Microphone",command=self.translation_mic).pack(side="left",padx=5); ttk.Button(bar,text="Speak Output",command=self.speak_translation).pack(side="left"); ttk.Button(bar,text="Refresh History",command=self.refresh_translation_history).pack(side="right")
        self.translation_output=tk.Text(self.section(tab,"Output"),height=6,wrap="word",font=("Segoe UI",12)); self.translation_output.master.pack(fill="both",expand=True,pady=5); self.translation_output.pack(fill="both",expand=True)
        hist=self.section(tab,"Translation History"); hist.pack(fill="both",expand=True); self.translation_tree=ttk.Treeview(hist,columns=("id","time","source","target","provider","text"),show="headings",height=5)
        for c,w in (("id",45),("time",145),("source",60),("target",60),("provider",110),("text",700)): self.translation_tree.heading(c,text=c.title()); self.translation_tree.column(c,width=w)
        self.translation_tree.pack(fill="both",expand=True)
    @staticmethod
    def lang_code(value): return value.split(' ',1)[0]
    def translate_text(self):
        text=self.translation_input.get('1.0','end').strip(); src=self.lang_code(self.source_lang.get()); dst=self.lang_code(self.target_lang.get())
        self.run_task("Translate",lambda:self.controller.translator.translate(text,src,dst,self.controller.user_id),self.show_translation)
    def show_translation(self,r): self.translation_output.delete('1.0','end'); self.translation_output.insert('1.0',f"Provider: {r.provider}\n\n{r.translated_text}"); self.hud.show(r.translated_text); self.refresh_translation_history()
    def translation_mic(self):
        code=self.lang_code(self.source_lang.get()); speech=LANGUAGES.get(code,{}).get('speech') or 'en-US'; self.run_task("Listening",lambda:self.controller.speech_to_text.listen_once(speech),lambda t:(self.translation_input.delete('1.0','end'),self.translation_input.insert('1.0',t)))
    def speak_translation(self): self.run_task("Speak",lambda:self.controller.text_to_speech.speak(self.translation_output.get('1.0','end').strip()))
    def refresh_translation_history(self):
        self.translation_tree.delete(*self.translation_tree.get_children())
        for r in self.controller.database.list_translations(self.controller.user_id): self.translation_tree.insert('', 'end',values=(r['id'],r['created_at'],r['source_language'],r['target_language'],r.get('provider',''),(r['translated_text'] or '')[:180]))

    # meetings
    def _build_meetings(self):
        tab=self.tabs['meetings']; form=self.section(tab,"Meeting Session"); form.pack(fill="x"); self.meeting_title=tk.StringVar(); self.meeting_participants=tk.StringVar(); self.meeting_speaker=tk.StringVar(); self.meeting_consent=tk.BooleanVar(); self.meeting_record_audio=tk.BooleanVar(); self.meeting_use_ai=tk.BooleanVar(value=True)
        ttk.Label(form,text="Title").grid(row=0,column=0,sticky='w'); ttk.Entry(form,textvariable=self.meeting_title,width=35).grid(row=0,column=1,sticky='ew',padx=5); ttk.Label(form,text="Participants (comma separated)").grid(row=0,column=2,sticky='w'); ttk.Entry(form,textvariable=self.meeting_participants,width=45).grid(row=0,column=3,sticky='ew',padx=5)
        ttk.Label(form,text="Current speaker").grid(row=1,column=0,sticky='w'); ttk.Entry(form,textvariable=self.meeting_speaker).grid(row=1,column=1,sticky='ew',padx=5); ttk.Checkbutton(form,text="Participants consented",variable=self.meeting_consent).grid(row=1,column=2,sticky='w'); ttk.Checkbutton(form,text="Record microphone audio",variable=self.meeting_record_audio).grid(row=1,column=3,sticky='w'); ttk.Checkbutton(form,text="Use Ask AI summary",variable=self.meeting_use_ai).grid(row=2,column=2,sticky='w')
        [form.columnconfigure(i,weight=1) for i in (1,3)]
        bar=ttk.Frame(tab); bar.pack(fill="x",pady=7); ttk.Button(bar,text="Start Session",command=self.start_meeting).pack(side="left"); ttk.Button(bar,text="Add Typed Utterance",command=self.add_typed_utterance).pack(side="left",padx=5); ttk.Button(bar,text="Listen One Utterance",command=self.listen_meeting).pack(side="left"); ttk.Button(bar,text="Finish & Save",command=self.finish_meeting).pack(side="left",padx=5); ttk.Button(bar,text="Save Typed Transcript",command=self.save_typed_meeting).pack(side="left")
        self.meeting_transcript=tk.Text(self.section(tab,"Transcript / Notes"),height=9,wrap="word",font=("Segoe UI",11)); self.meeting_transcript.master.pack(fill="both",expand=True); self.meeting_transcript.pack(fill="both",expand=True)
        hist=self.section(tab,"Meeting History"); hist.pack(fill="both",expand=True,pady=(8,0)); hb=ttk.Frame(hist); hb.pack(fill="x"); ttk.Button(hb,text="Refresh",command=self.refresh_meetings).pack(side="left"); ttk.Button(hb,text="View",command=self.view_meeting).pack(side="left",padx=5); ttk.Button(hb,text="Export TXT",command=lambda:self.export_meeting('txt')).pack(side="left"); ttk.Button(hb,text="Export JSON",command=lambda:self.export_meeting('json')).pack(side="left",padx=5); ttk.Button(hb,text="Delete",command=self.delete_meeting).pack(side="left")
        self.meeting_tree=ttk.Treeview(hist,columns=("id","title","started","participants","summary"),show="headings",height=5)
        for c,w in (("id",45),("title",170),("started",150),("participants",220),("summary",600)): self.meeting_tree.heading(c,text=c.title()); self.meeting_tree.column(c,width=w)
        self.meeting_tree.pack(fill="both",expand=True,pady=5)
    def participants(self): return [x.strip() for x in self.meeting_participants.get().split(',') if x.strip()]
    def start_meeting(self):
        self.run_task("Start meeting",lambda:self.controller.meetings.start_session(self.meeting_title.get(),self.participants(),self.lang_code(self.source_lang.get()),self.lang_code(self.target_lang.get()),self.meeting_consent.get(),self.meeting_record_audio.get()),lambda _r:messagebox.showinfo("Meeting","Session started",parent=self.root))
    def add_typed_utterance(self):
        text=simpledialog.askstring("Utterance","What was said?",parent=self.root)
        if text:
            item=self.controller.meetings.add_utterance(text,self.meeting_speaker.get(),self.lang_code(self.source_lang.get()),self.controller.user_id); self.meeting_transcript.insert('end',f"[{self.meeting_speaker.get() or 'Speaker'}] {item['text']}\n" + (f"  → {item['translation']}\n" if item['translation'] else ''))
    def listen_meeting(self):
        code=self.lang_code(self.source_lang.get()); speech=LANGUAGES.get(code,{}).get('speech') or 'en-US'; self.run_task("Listen utterance",lambda:self.controller.meetings.listen_utterance(self.meeting_speaker.get(),speech,self.controller.user_id),lambda item:self.meeting_transcript.insert('end',f"[{self.meeting_speaker.get() or 'Speaker'}] {item['text']}\n" + (f"  → {item['translation']}\n" if item['translation'] else '')))
    def finish_meeting(self): self.run_task("Finish meeting",lambda:self.controller.meetings.finish_session(self.meeting_use_ai.get(),self.controller.user_id,True),self.show_meeting_result)
    def save_typed_meeting(self): self.run_task("Save meeting",lambda:self.controller.meetings.save_meeting(self.meeting_title.get(),self.participants(),self.meeting_transcript.get('1.0','end').strip(),self.lang_code(self.source_lang.get()),self.lang_code(self.target_lang.get()),self.meeting_consent.get(),self.meeting_use_ai.get(),self.controller.user_id),self.show_meeting_result)
    def show_meeting_result(self,r): self.refresh_meetings(); self.text_dialog("Meeting Result",f"SUMMARY\n{r.summary}\n\nDECISIONS\n"+'\n'.join(r.decisions)+"\n\nTASKS\n"+'\n'.join(r.tasks)+f"\n\nTRANSLATION\n{r.translated_transcript}")
    def refresh_meetings(self):
        self.meeting_tree.delete(*self.meeting_tree.get_children())
        for r in self.controller.meetings.list_meetings(): self.meeting_tree.insert('', 'end',values=(r['id'],r['title'],r['started_at'],r.get('participants',''),(r.get('summary') or '')[:220]))
    def selected_meeting_id(self):
        v=self._selected(self.meeting_tree); return int(v[0]) if v else None
    def view_meeting(self):
        mid=self.selected_meeting_id()
        if mid:
            r=self.controller.meetings.get_meeting(mid); self.text_dialog(r['title'],json.dumps(r,ensure_ascii=False,indent=2,default=str))
    def export_meeting(self,fmt):
        mid=self.selected_meeting_id()
        if mid: path=self.controller.meetings.export_meeting(mid,fmt); messagebox.showinfo("Export",str(path),parent=self.root)
    def delete_meeting(self):
        mid=self.selected_meeting_id()
        if mid and messagebox.askyesno("Delete","Delete meeting?",parent=self.root): self.controller.meetings.delete_meeting(mid); self.refresh_meetings()

    # AI
    def _build_ai(self):
        tab=self.tabs['ask_ai']; ttk.Label(tab,text="Ask AI is connected to health, privacy, people, meetings and troubleshooting. Cloud use requires API key and explicit permission.",wraplength=1100).pack(fill="x")
        self.ai_question=tk.Text(tab,height=5,wrap="word",font=("Segoe UI",12)); self.ai_question.pack(fill="x",pady=8); bar=ttk.Frame(tab); bar.pack(fill="x"); ttk.Button(bar,text="Ask AI",command=self.ask_ai).pack(side="left"); ttk.Button(bar,text="Run as Assistant Command",command=self.run_command).pack(side="left",padx=5); ttk.Button(bar,text="Refresh History",command=self.refresh_ai_history).pack(side="left")
        self.ai_answer=tk.Text(tab,height=12,wrap="word",font=("Segoe UI",11)); self.ai_answer.pack(fill="both",expand=True,pady=8)
        self.ai_tree=ttk.Treeview(tab,columns=("id","time","provider","question"),show="headings",height=5)
        for c,w in (("id",45),("time",150),("provider",120),("question",850)): self.ai_tree.heading(c,text=c.title()); self.ai_tree.column(c,width=w)
        self.ai_tree.pack(fill="both",expand=True)
    def ask_ai(self): self.run_task("Ask AI",lambda:self.controller.ai_service.ask(self.ai_question.get('1.0','end').strip(),context=self.controller.ai_context(),user_id=self.controller.user_id),self.show_ai)
    def run_command(self): self.run_task("Assistant command",lambda:self.controller.assistant.handle_text_command(self.ai_question.get('1.0','end').strip(),self.controller.user_id),lambda t:self.show_ai(type('R',(),{'provider':'assistant-core','answer':t})()))
    def show_ai(self,r): self.ai_answer.delete('1.0','end'); self.ai_answer.insert('1.0',f"Provider: {r.provider}\n\n{r.answer}"); self.hud.show(r.answer[:300]); self.refresh_ai_history()
    def refresh_ai_history(self):
        self.ai_tree.delete(*self.ai_tree.get_children())
        for r in self.controller.database.list_ai_history(self.controller.user_id): self.ai_tree.insert('', 'end',values=(r['id'],r['created_at'],r['provider'],r['question'][:220]))

    # security
    def _build_security(self):
        tab=self.tabs['security']; bar=ttk.Frame(tab); bar.pack(fill="x"); ttk.Button(bar,text="Refresh Logs",command=self.refresh_security).pack(side="left"); ttk.Button(bar,text="Change Password",command=self.change_password).pack(side="left",padx=5)
        if (self.controller.current_user or {}).get('role')=='admin': ttk.Button(bar,text="Create User",command=self.create_user).pack(side="left"); ttk.Button(bar,text="Refresh Users",command=self.refresh_users).pack(side="left",padx=5); ttk.Button(bar,text="Enable/Disable Selected",command=self.toggle_user).pack(side="left")
        panes=ttk.Panedwindow(tab,orient='vertical'); panes.pack(fill="both",expand=True,pady=8); logs=self.section(panes,"Security Logs"); users=self.section(panes,"Users"); panes.add(logs,weight=3); panes.add(users,weight=2)
        self.security_tree=ttk.Treeview(logs,columns=("id","time","severity","event","message"),show="headings");
        for c,w in (("id",45),("time",155),("severity",70),("event",150),("message",750)): self.security_tree.heading(c,text=c.title()); self.security_tree.column(c,width=w)
        self.security_tree.pack(fill="both",expand=True)
        self.users_tree=ttk.Treeview(users,columns=("id","username","name","role","language","active","last_login"),show="headings")
        for c,w in (("id",45),("username",120),("name",170),("role",75),("language",70),("active",65),("last_login",170)): self.users_tree.heading(c,text=c.title()); self.users_tree.column(c,width=w)
        self.users_tree.pack(fill="both",expand=True)
    def refresh_security(self):
        self.security_tree.delete(*self.security_tree.get_children())
        for r in self.controller.database.list_security_logs(): self.security_tree.insert('', 'end',values=(r['id'],r['created_at'],r['severity'],r['event_type'],r['message']))
    def refresh_users(self):
        self.users_tree.delete(*self.users_tree.get_children())
        for r in self.controller.database.list_users(): self.users_tree.insert('', 'end',values=(r['id'],r['username'],r['full_name'],r['role'],r['preferred_language'],"Yes" if r['is_active'] else "No",r.get('last_login') or ''))
    def change_password(self):
        old=simpledialog.askstring("Current","Current password:",show='*',parent=self.root); new=simpledialog.askstring("New","New strong password:",show='*',parent=self.root) if old is not None else None
        if new:
            try: self.controller.security.change_password(self.controller.user_id or 0,old or '',new); messagebox.showinfo("Password","Changed successfully",parent=self.root)
            except Exception as exc: messagebox.showerror("Password",str(exc),parent=self.root)
    def create_user(self):
        u=simpledialog.askstring("Username","Username:",parent=self.root); n=simpledialog.askstring("Name","Full name:",parent=self.root) if u else None; p=simpledialog.askstring("Password","Strong temporary password:",show='*',parent=self.root) if n else None; role=simpledialog.askstring("Role","admin, user or viewer:",initialvalue='user',parent=self.root) if p else None
        if u and n and p and role:
            try: self.controller.security.create_user(u,p,n,role,self.language); self.refresh_users()
            except Exception as exc: messagebox.showerror("Create User",str(exc),parent=self.root)
    def toggle_user(self):
        v=self._selected(self.users_tree)
        if v:
            active=v[5]=='Yes'; self.controller.database.set_user_active(int(v[0]),not active); self.controller.security.audit("USER_STATUS",f"Set {v[1]} active={not active}",user_id=self.controller.user_id); self.refresh_users()

    # data control
    def _build_data_control(self):
        tab=self.tabs['data_control']; controls=self.section(tab,"Control System Data Tools"); controls.pack(fill="x"); self.backup_media=tk.BooleanVar(); self.backup_encrypted=tk.BooleanVar()
        ttk.Checkbutton(controls,text="Include images and audio",variable=self.backup_media).grid(row=0,column=0,sticky='w'); ttk.Checkbutton(controls,text="Encrypt backup",variable=self.backup_encrypted).grid(row=0,column=1,sticky='w'); ttk.Button(controls,text="Create Backup",command=self.create_backup).grid(row=0,column=2,padx=5); ttk.Button(controls,text="Restore Selected Backup",command=self.restore_backup).grid(row=0,column=3,padx=5); ttk.Button(controls,text="Scan Devices",command=self.scan_devices).grid(row=0,column=4,padx=5); ttk.Button(controls,text="Export All JSON",command=self.export_all_data).grid(row=0,column=5,padx=5); ttk.Button(controls,text="System Report",command=self.system_report).grid(row=0,column=6,padx=5); ttk.Button(controls,text="Refresh",command=self.refresh_data_control).grid(row=0,column=7,padx=5)
        panes=ttk.Panedwindow(tab,orient='horizontal'); panes.pack(fill="both",expand=True,pady=10); backups=self.section(panes,"Backups"); reminders=self.section(panes,"Reminders"); devices=self.section(panes,"Device History"); panes.add(backups,weight=2); panes.add(reminders,weight=2); panes.add(devices,weight=2)
        self.backup_tree=ttk.Treeview(backups,columns=("name","size"),show="headings"); self.backup_tree.heading('name',text='Backup'); self.backup_tree.heading('size',text='Size KB'); self.backup_tree.column('name',width=280); self.backup_tree.pack(fill="both",expand=True)
        rb=ttk.Frame(reminders); rb.pack(fill="x"); ttk.Button(rb,text="Add Reminder",command=self.add_reminder).pack(side="left"); ttk.Button(rb,text="Complete",command=self.complete_reminder).pack(side="left",padx=5)
        self.reminder_tree=ttk.Treeview(reminders,columns=("id","title","due","done"),show="headings");
        for c,w in (("id",40),("title",200),("due",140),("done",55)): self.reminder_tree.heading(c,text=c.title()); self.reminder_tree.column(c,width=w)
        self.reminder_tree.pack(fill="both",expand=True,pady=5)
        self.device_tree=ttk.Treeview(devices,columns=("time","type","name","status"),show="headings");
        for c,w in (("time",145),("type",80),("name",160),("status",90)): self.device_tree.heading(c,text=c.title()); self.device_tree.column(c,width=w)
        self.device_tree.pack(fill="both",expand=True)
    def create_backup(self): self.run_task("Create backup",lambda:self.controller.backups.create_backup(self.backup_media.get(),self.backup_encrypted.get()),lambda p:(self.refresh_data_control(),messagebox.showinfo("Backup",str(p),parent=self.root)))
    def restore_backup(self):
        v=self._selected(self.backup_tree)
        if v and messagebox.askyesno("Restore","Restore backup over current project data?",parent=self.root): self.controller.backups.restore_backup(self.controller.backups.list_backups()[self.backup_tree.index(self.backup_tree.selection()[0])]); messagebox.showinfo("Restore","Restore completed. Restart application.",parent=self.root)
    def scan_devices(self): self.run_task("Scan devices",self.controller.devices.scan,lambda r:(self.text_dialog("Devices",json.dumps(r,ensure_ascii=False,indent=2)),self.refresh_data_control()))
    def export_all_data(self): self.run_task("Export all data",self.controller.data_control.export_all_json,lambda p:messagebox.showinfo("Export",str(p),parent=self.root))
    def system_report(self): self.run_task("System report",lambda:self.controller.data_control.system_report(self.controller.health_check(True),self.controller.privacy.export()),lambda p:messagebox.showinfo("Report",str(p),parent=self.root))
    def add_reminder(self):
        title=simpledialog.askstring("Reminder","Title:",parent=self.root); due=simpledialog.askstring("Due","Date/time YYYY-MM-DD HH:MM (optional):",parent=self.root) if title else None
        if title: self.controller.reminders.add(self.controller.user_id or 0,title,due or None); self.refresh_data_control()
    def complete_reminder(self):
        v=self._selected(self.reminder_tree)
        if v: self.controller.reminders.complete(int(v[0]),True); self.refresh_data_control()
    def refresh_data_control(self):
        self.backup_tree.delete(*self.backup_tree.get_children())
        for p in self.controller.backups.list_backups(): self.backup_tree.insert('', 'end',values=(p.name,round(p.stat().st_size/1024,1)))
        self.reminder_tree.delete(*self.reminder_tree.get_children())
        if self.controller.user_id:
            for r in self.controller.reminders.list(self.controller.user_id): self.reminder_tree.insert('', 'end',values=(r['id'],r['title'],r.get('due_at') or '',"Yes" if r.get('completed') else "No"))
        self.device_tree.delete(*self.device_tree.get_children())
        for r in self.controller.database.list_device_events(): self.device_tree.insert('', 'end',values=(r['created_at'],r.get('device_type',''),r.get('device_name',''),r.get('status','')))

    # settings
    def _build_settings(self):
        tab=self.tabs['settings']; box=self.section(tab,"Privacy Permissions"); box.pack(fill="x"); self.privacy_vars={}; labels={"camera":"Allow camera","microphone":"Allow microphone","face_recognition":"Allow face recognition","save_unknown_faces":"Save unknown faces","meeting_recording":"Allow meeting storage/recording","cloud_ai":"Allow typed content to cloud AI","location":"Allow location services","notifications":"Allow notifications"}
        for i,(key,label) in enumerate(labels.items()): self.privacy_vars[key]=tk.BooleanVar(); ttk.Checkbutton(box,text=label,variable=self.privacy_vars[key]).grid(row=i//2,column=i%2,sticky='w',padx=10,pady=4)
        ttk.Button(box,text="Save Privacy Settings",command=self.save_privacy).grid(row=4,column=0,sticky='w',pady=10)
        lang=self.section(tab,"Interface Language"); lang.pack(fill="x",pady=10); self.ui_lang=tk.StringVar(value=self.language); ttk.Combobox(lang,textvariable=self.ui_lang,state='readonly',values=('ar','en','fr','rw'),width=20).pack(side='left'); ttk.Label(lang,text="Applies after logout/login").pack(side='left',padx=10)
        ttk.Label(tab,text="Face recognition and emotion estimation can be inaccurate. Do not use them alone for medical, legal, employment, policing, or other high-stakes decisions. Always obtain consent before recording or storing personal data.",wraplength=1150,foreground="#b45309").pack(fill="x",pady=10)
    def load_privacy(self):
        p=self.controller.privacy.get_permissions(); [v.set(bool(p.get(k,False))) for k,v in self.privacy_vars.items()]
    def save_privacy(self): self.controller.privacy.update({k:v.get() for k,v in self.privacy_vars.items()}); self.controller.database.set_setting('ui_language',self.ui_lang.get(),self.controller.user_id); messagebox.showinfo("Settings","Saved",parent=self.root)

    def refresh_all(self):
        tasks=(
            ("dashboard",self.refresh_dashboard),
            ("people",self.refresh_people),
            ("face workflow",self.update_face_workflow),
            ("unknown events",self.refresh_unknown),
            ("translation history",self.refresh_translation_history),
            ("meetings",self.refresh_meetings),
            ("AI history",self.refresh_ai_history),
            ("security",self.refresh_security),
            ("users",self.refresh_users),
            ("data control",self.refresh_data_control),
            ("privacy",self.load_privacy),
        )
        errors=[]
        for name,function in tasks:
            try:
                function()
            except Exception as exc:
                errors.append(f"{name}: {exc}")
                log.exception("Initial refresh failed: %s",name)
        if errors:
            self.status_var.set("Loaded with warnings — see logs/system.log")
        else:
            self.status_var.set(tr("ready",self.language))
    def logout(self): self.controller.logout(); self.hud.window.destroy(); self.root.destroy(); self.login_root.deiconify()
    def exit_application(self): self.controller.shutdown(); self.login_root.destroy()