from __future__ import annotations

import re
import wave
import audioop
from collections import Counter
from pathlib import Path

from .models import AudioFeatureResult, FillerStats

FILLER_WORDS: tuple[str, ...] = (
    "um",
    "uh",
    "er",
    "ah",
    "hmm",
    "like",
    "actually",
    "basically",
    "literally",
    "so",
    "okay",
    "right",
    "you know",
    "i mean",
)


def analyze_filler_words(transcript: str) -> FillerStats:
    text = f" {transcript.lower()} "
    words = re.findall(r"[a-zA-Z]+(?:'[a-z]+)?", transcript.lower())
    total_words = len(words)
    occurrences: Counter[str] = Counter()

    for filler in FILLER_WORDS:
        if " " in filler:
            pattern = rf"(?<![a-z]){re.escape(filler)}(?![a-z])"
            count = len(re.findall(pattern, text))
        else:
            count = sum(1 for word in words if word == filler)
        if count:
            occurrences[filler] = count

    filler_count = sum(occurrences.values())
    filler_ratio = filler_count / total_words if total_words else 0.0
    return FillerStats(
        filler_word_count=filler_count,
        total_words=total_words,
        filler_ratio=filler_ratio,
        occurrences=dict(occurrences),
    )


def _extract_with_wave(audio_path: Path) -> AudioFeatureResult:
    warnings = ["librosa is not installed; used WAV-only fallback audio analysis."]
    try:
        with wave.open(str(audio_path), "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            channels = wav_file.getnchannels()
            frame_count = wav_file.getnframes()
    except Exception as exc:
        return AudioFeatureResult(
            duration_sec=0.0,
            pause_ratio=0.0,
            rms_energy=0.0,
            zero_crossing_rate=0.0,
            warnings=[f"Audio analysis unavailable: {exc}"],
        )

    duration = frame_count / sample_rate if sample_rate else 0.0
    try:
        import numpy as np
    except ModuleNotFoundError:
        max_possible = float((2 ** (8 * sample_width - 1)) or 1)
        try:
            rms = audioop.rms(frames, sample_width) / max_possible
        except Exception:
            rms = 0.0
        return AudioFeatureResult(
            duration_sec=duration,
            pause_ratio=0.0,
            rms_energy=float(rms),
            zero_crossing_rate=0.0,
            sample_rate=sample_rate,
            warnings=warnings
            + ["NumPy is not installed; pause and zero-crossing metrics were skipped."],
        )

    if sample_width == 1:
        dtype = np.uint8
        midpoint = 128
    elif sample_width == 2:
        dtype = np.int16
        midpoint = 0
    else:
        return AudioFeatureResult(
            duration_sec=frame_count / sample_rate if sample_rate else 0.0,
            pause_ratio=0.0,
            rms_energy=0.0,
            zero_crossing_rate=0.0,
            sample_rate=sample_rate,
            warnings=warnings + [f"Unsupported WAV sample width: {sample_width} bytes."],
        )

    audio = np.frombuffer(frames, dtype=dtype).astype(np.float32) - midpoint
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    max_abs = np.max(np.abs(audio)) or 1.0
    y = audio / max_abs
    rms = float(np.sqrt(np.mean(np.square(y)))) if y.size else 0.0
    zcr = float(np.mean(np.abs(np.diff(np.signbit(y))).astype(float))) if y.size else 0.0

    if y.size and duration:
        frame_size = max(1, int(sample_rate * 0.03))
        frames_rms = [
            float(np.sqrt(np.mean(np.square(y[index : index + frame_size]))))
            for index in range(0, len(y), frame_size)
        ]
        silence_threshold = max(0.015, rms * 0.35)
        silent_frames = sum(1 for value in frames_rms if value < silence_threshold)
        pause_ratio = silent_frames / len(frames_rms) if frames_rms else 0.0
    else:
        pause_ratio = 0.0

    return AudioFeatureResult(
        duration_sec=duration,
        pause_ratio=max(0.0, min(1.0, pause_ratio)),
        rms_energy=rms,
        zero_crossing_rate=zcr,
        sample_rate=sample_rate,
        warnings=warnings,
    )


def extract_audio_features(audio_path: str | Path) -> AudioFeatureResult:
    path = Path(audio_path)
    try:
        import librosa
        import numpy as np
    except ModuleNotFoundError:
        return _extract_with_wave(path)

    try:
        y, sr = librosa.load(str(path), sr=None, mono=True)
        duration = float(librosa.get_duration(y=y, sr=sr)) if y.size else 0.0
        rms_values = librosa.feature.rms(y=y)[0] if y.size else np.array([0.0])
        rms_energy = float(np.mean(rms_values))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=y)[0])) if y.size else 0.0

        if y.size and duration > 0:
            intervals = librosa.effects.split(y, top_db=30)
            voiced = sum((end - start) / sr for start, end in intervals)
            pause_ratio = max(0.0, min(1.0, 1.0 - (voiced / duration)))
        else:
            pause_ratio = 0.0

        return AudioFeatureResult(
            duration_sec=duration,
            pause_ratio=pause_ratio,
            rms_energy=rms_energy,
            zero_crossing_rate=zcr,
            sample_rate=int(sr) if sr else None,
        )
    except Exception as exc:  # pragma: no cover - depends on local audio codecs
        fallback = _extract_with_wave(path)
        fallback.warnings.append(f"Librosa analysis failed: {exc}")
        return fallback
