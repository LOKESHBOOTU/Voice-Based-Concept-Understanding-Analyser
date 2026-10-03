from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = Path(os.getenv("VBCUA_UPLOAD_DIR", BASE_DIR / "uploads"))
REPORT_DIR = Path(os.getenv("VBCUA_REPORT_DIR", BASE_DIR / "reports"))
DB_PATH = Path(os.getenv("VBCUA_DB_PATH", BASE_DIR / "vbcua.sqlite3"))

WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base")
SENTENCE_MODEL_NAME = os.getenv(
    "SENTENCE_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def configure_ffmpeg_path() -> None:
    try:
        import shutil
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        bin_dir = os.path.dirname(exe)
        target = os.path.join(bin_dir, "ffmpeg.exe")
        if not os.path.exists(target) and os.path.exists(exe):
            shutil.copyfile(exe, target)
        if bin_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass


def ensure_runtime_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    configure_ffmpeg_path()
