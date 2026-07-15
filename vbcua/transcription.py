from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .config import WHISPER_MODEL_NAME
from .models import TranscriptionResult


@lru_cache(maxsize=2)
def _load_whisper_model(model_name: str):
    import whisper

    return whisper.load_model(model_name)


def transcribe_audio(
    audio_path: str | Path,
    *,
    model_name: str = WHISPER_MODEL_NAME,
    transcript_override: str | None = None,
) -> TranscriptionResult:
    """Transcribe an audio file with Whisper, or use a provided transcript."""

    cleaned_override = (transcript_override or "").strip()
    if cleaned_override:
        return TranscriptionResult(text=cleaned_override, engine="manual transcript")

    try:
        model = _load_whisper_model(model_name)
        result = model.transcribe(str(audio_path), fp16=False)
    except ModuleNotFoundError:
        return TranscriptionResult(
            text="",
            engine="unavailable",
            warnings=[
                "OpenAI Whisper is not installed. Add a manual transcript or install requirements.txt."
            ],
        )
    except Exception as exc:  # pragma: no cover - depends on local model runtime
        return TranscriptionResult(
            text="",
            engine="whisper",
            warnings=[f"Transcription failed: {exc}"],
        )

    return TranscriptionResult(
        text=str(result.get("text", "")).strip(),
        engine=f"openai-whisper:{model_name}",
    )
