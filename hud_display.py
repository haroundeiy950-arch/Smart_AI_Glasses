"""Small always-on-top HUD simulator for the future glasses display."""
from __future__ import annotations
import tkinter as tk

class HUDDisplay:
    def __init__(self,parent: tk.Misc):
        self.window=tk.Toplevel(parent); self.window.title("Smart Glasses HUD"); self.window.geometry("620x180+30+30"); self.window.attributes('-topmost',True); self.window.configure(bg='black')
        self.text=tk.StringVar(value="Smart AI Glasses ready")
        tk.Label(self.window,textvariable=self.text,bg='black',fg='#00ff99',font=('Segoe UI',18,'bold'),wraplength=580,justify='left').pack(fill='both',expand=True,padx=20,pady=20)
        self.window.withdraw()
    def show(self,message: str): self.text.set(message); self.window.deiconify(); self.window.lift()
    def hide(self): self.window.withdraw()
