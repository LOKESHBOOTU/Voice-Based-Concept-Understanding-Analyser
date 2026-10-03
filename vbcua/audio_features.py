from __future__ import annotations

import audioop
from collections import Counter
from io import BytesIO
from pathlib import Path
import re
import wave

from .models import AudioFeatureResult, FillerStats, SpeechProsodyResult

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


def analyze_speech_prosody(
    transcript: str,
    duration_sec: float,
    pause_ratio: float = 0.0,
    audio_data: any = None,
    sample_rate: int = 16000,
) -> SpeechProsodyResult:
    """Computes speech prosody: pacing (WPM), pitch variation, cadence, and articulation rate."""
    words = re.findall(r"[a-zA-Z]+(?:'[a-z]+)?", transcript.lower())
    total_words = len(words)

    # 1. Speaking Pace (Words Per Minute)
    if duration_sec > 0:
        wpm = round((total_words / duration_sec) * 60.0, 1)
    else:
        wpm = 0.0

    if wpm < 105:
        pacing_cat = "Sluggish Pace (Too Slow)"
    elif wpm <= 165:
        pacing_cat = "Optimal Conversational Pace"
    else:
        pacing_cat = "Rushed Delivery (Too Fast)"

    # 2. Articulation Rate (words per active speaking second)
    speaking_time = max(0.5, duration_sec * (1.0 - pause_ratio))
    articulation_rate = round(total_words / speaking_time, 2) if speaking_time else 0.0

    # 3. Pitch Variation (F0 standard deviation)
    pitch_var = 28.5  # Standard human conversational default (Hz)
    pitch_label = "Balanced & Natural Cadence"

    try:
        import numpy as np

        if audio_data is not None and isinstance(audio_data, np.ndarray) and audio_data.size > 1000:
            # Estimate pitch via zero-crossings and auto-correlation on voiced chunks
            frame_len = int(sample_rate * 0.04)  # 40ms frames
            step = int(frame_len / 2)
            pitches = []
            for i in range(0, len(audio_data) - frame_len, step):
                chunk = audio_data[i : i + frame_len]
                if np.max(np.abs(chunk)) > 0.03:  # Voiced threshold
                    # Zero-crossing estimation of fundamental frequency
                    zc = np.sum(np.abs(np.diff(np.signbit(chunk))))
                    f0 = (zc * sample_rate) / (2 * frame_len)
                    if 70 <= f0 <= 350:  # Valid human vocal pitch range
                        pitches.append(f0)
            if len(pitches) > 5:
                pitch_var = float(np.std(pitches))

            if pitch_var < 18.0:
                pitch_label = "Monotone Delivery (Needs vocal inflection)"
            elif pitch_var <= 45.0:
                pitch_label = "Balanced & Natural Cadence"
            else:
                pitch_label = "Dynamic & Expressive Cadence"
    except Exception:
        pass

    # 4. Hesitation Clusters (based on pauses and filler count)
    filler_stats = analyze_filler_words(transcript)
    hesitation_clusters = int(filler_stats.filler_word_count + (pause_ratio * duration_sec // 2))

    return SpeechProsodyResult(
        words_per_minute=wpm,
        pacing_category=pacing_cat,
        pitch_variation_hz=round(pitch_var, 1),
        pitch_expressiveness=pitch_label,
        hesitation_clusters=hesitation_clusters,
        articulation_rate=articulation_rate,
    )


def create_spectrogram_png(audio_path: str | Path) -> bytes | None:
    """Generates an audio frequency spectrogram image buffer."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        path = Path(audio_path)
        with wave.open(str(path), "rb") as wf:
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())
            channels = wf.getnchannels()

        dtype = np.int16 if sample_width == 2 else (np.uint8 if sample_width == 1 else np.int32)
        audio = np.frombuffer(frames, dtype=dtype).astype(np.float32)
        if sample_width == 1:
            audio -= 128
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)

        max_val = np.max(np.abs(audio)) or 1.0
        y = (audio / max_val) + 1e-6

        fig, ax = plt.subplots(figsize=(9, 2.6), dpi=150)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            ax.specgram(y, Fs=sample_rate, cmap="magma", NFFT=512, noverlap=256)
        ax.set_title("Frequency Spectrogram (Speech Prosody & Formants)", fontsize=10, pad=6)
        ax.set_xlabel("Time (s)", fontsize=9)
        ax.set_ylabel("Frequency (Hz)", fontsize=9)
        fig.tight_layout()

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        plt.close(fig)
        return buffer.getvalue()
    except Exception:
        return None


def _extract_with_wave(audio_path: Path) -> AudioFeatureResult:
    warnings = ["Used WAV-based audio analysis engine."]
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
            warnings=warnings + ["NumPy is not installed; pause and zero-crossing metrics were skipped."],
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

    prosody = analyze_speech_prosody("", duration, pause_ratio, y, sample_rate)

    return AudioFeatureResult(
        duration_sec=duration,
        pause_ratio=max(0.0, min(1.0, pause_ratio)),
        rms_energy=rms,
        zero_crossing_rate=zcr,
        sample_rate=sample_rate,
        prosody=prosody,
        warnings=warnings,
    )


def extract_audio_features(audio_path: str | Path, transcript: str = "") -> AudioFeatureResult:
    path = Path(audio_path)
    try:
        import librosa
        import numpy as np
    except ModuleNotFoundError:
        result = _extract_with_wave(path)
        if transcript:
            result.prosody = analyze_speech_prosody(transcript, result.duration_sec, result.pause_ratio)
        return result

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

        prosody = analyze_speech_prosody(transcript, duration, pause_ratio, y, int(sr) if sr else 16000)

        return AudioFeatureResult(
            duration_sec=duration,
            pause_ratio=pause_ratio,
            rms_energy=rms_energy,
            zero_crossing_rate=zcr,
            sample_rate=int(sr) if sr else None,
            prosody=prosody,
        )
    except Exception as exc:
        fallback = _extract_with_wave(path)
        if transcript:
            fallback.prosody = analyze_speech_prosody(transcript, fallback.duration_sec, fallback.pause_ratio)
        fallback.warnings.append(f"Primary audio loader fallback: {exc}")
        return fallback
