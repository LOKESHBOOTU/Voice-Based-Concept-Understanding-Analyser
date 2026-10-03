from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .config import WHISPER_MODEL_NAME, configure_ffmpeg_path
from .models import TranscriptionResult


@lru_cache(maxsize=2)
def _load_whisper_model(model_name: str):
    import whisper

    return whisper.load_model(model_name)


def _load_audio_numpy(audio_path: Path):
    """Loads a WAV audio file into a 16kHz float32 NumPy array without calling ffmpeg."""
    import wave
    import numpy as np

    with wave.open(str(audio_path), "rb") as wf:
        sr = wf.getframerate()
        sw = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())
        ch = wf.getnchannels()

    dtype = np.int16 if sw == 2 else (np.uint8 if sw == 1 else np.int32)
    audio = np.frombuffer(frames, dtype=dtype).astype(np.float32)
    if sw == 1:
        audio -= 128
        audio /= 128.0
    elif sw == 2:
        audio /= 32768.0
    elif sw == 4:
        audio /= 2147483648.0

    if ch > 1:
        audio = audio.reshape(-1, ch).mean(axis=1)

    # Resample to 16000 Hz if necessary
    if sr != 16000 and len(audio) > 0:
        new_len = int(len(audio) * 16000 / sr)
        audio = np.interp(
            np.linspace(0, len(audio), new_len, endpoint=False),
            np.arange(len(audio)),
            audio,
        ).astype(np.float32)

    return audio


def _transcribe_with_speech_recognition(audio_path: Path) -> str | None:
    """Fast fallback transcription using SpeechRecognition (Google Web Speech API)."""
    try:
        import speech_recognition as sr

        r = sr.Recognizer()
        with sr.AudioFile(str(audio_path)) as source:
            audio_data = r.record(source)
        text = r.recognize_google(audio_data)
        return str(text).strip()
    except Exception:
        return None


def transcribe_audio(
    audio_path: str | Path,
    *,
    model_name: str = WHISPER_MODEL_NAME,
    transcript_override: str | None = None,
) -> TranscriptionResult:
    """Multi-tier resilient audio transcription: Manual -> OpenAI Whisper -> SpeechRecognition Fallback."""
    cleaned_override = (transcript_override or "").strip()
    if cleaned_override:
        return TranscriptionResult(text=cleaned_override, engine="manual transcript")

    path = Path(audio_path)
    configure_ffmpeg_path()
    whisper_warnings: list[str] = []

    # Tier 1: Try OpenAI Whisper
    try:
        model = _load_whisper_model(model_name)
        try:
            result = model.transcribe(str(path), fp16=False)
            text = str(result.get("text", "")).strip()
        except Exception:
            # Fallback to direct NumPy decoding if ffmpeg subprocess had issues
            audio_np = _load_audio_numpy(path)
            result = model.transcribe(audio_np, fp16=False)
            text = str(result.get("text", "")).strip()

        if text:
            return TranscriptionResult(
                text=text,
                engine=f"openai-whisper:{model_name}",
            )
    except ModuleNotFoundError:
        whisper_warnings.append("OpenAI Whisper is not installed.")
    except Exception as exc:
        whisper_warnings.append(f"Whisper inference failed: {exc}")

    # Tier 2: Try SpeechRecognition (Google Web Speech API)
    sr_text = _transcribe_with_speech_recognition(path)
    if sr_text:
        return TranscriptionResult(
            text=sr_text,
            engine="google-speech-recognition (fallback)",
            warnings=whisper_warnings,
        )

    # Tier 3: All engines unavailable or failed
    return TranscriptionResult(
        text="",
        engine="unavailable",
        warnings=whisper_warnings + [
            "Automatic speech recognition was unavailable for this audio file. Please ensure internet access or provide a manual transcript in the expander."
        ],
    )
