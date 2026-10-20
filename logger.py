"""Rotating application logs."""
from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config import LOGS_DIR, ensure_project_folders

_CONFIGURED = False

def _handler(path: Path, level: int = logging.INFO) -> RotatingFileHandler:
    h = RotatingFileHandler(path, maxBytes=3_000_000, backupCount=5, encoding="utf-8")
    h.setLevel(level)
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    return h

def configure_logging(debug: bool = False) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    ensure_project_folders()
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    root.addHandler(_handler(LOGS_DIR / "system.log", logging.DEBUG if debug else logging.INFO))
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if debug else logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root.addHandler(console)
    for name, filename in (("security", "security.log"), ("meetings", "meetings.log"), ("ai", "ai.log")):
        lg = logging.getLogger(name)
        lg.setLevel(logging.INFO)
        lg.addHandler(_handler(LOGS_DIR / filename))
        lg.propagate = False
    _CONFIGURED = True

def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
