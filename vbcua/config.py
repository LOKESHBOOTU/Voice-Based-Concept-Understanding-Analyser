from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_DIR = BASE_DIR / "reports"
DB_PATH = Path(os.getenv("VBCUA_DB_PATH", BASE_DIR / "vbcua.sqlite3"))

WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base")
SENTENCE_MODEL_NAME = os.getenv(
    "SENTENCE_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def ensure_runtime_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
