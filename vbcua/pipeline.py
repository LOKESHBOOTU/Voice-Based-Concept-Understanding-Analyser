from __future__ import annotations

from pathlib import Path

from .audio_features import analyze_filler_words, extract_audio_features
from .models import AnalysisResult, ReferenceConcept
from .scoring import score_analysis
from .semantic import evaluate_semantic_understanding
from .summary import generate_summary
from .text_analysis import analyze_sentiment
from .transcription import transcribe_audio


def analyze_audio(
    audio_path: str | Path,
    concept: ReferenceConcept,
    *,
    transcript_override: str | None = None,
    use_gemini_summary: bool = False,
) -> AnalysisResult:
    path = Path(audio_path)
    transcript = transcribe_audio(path, transcript_override=transcript_override)
    filler_stats = analyze_filler_words(transcript.text)
    audio_features = extract_audio_features(path)
    semantic = evaluate_semantic_understanding(transcript.text, concept)
    sentiment = analyze_sentiment(transcript.text)
    score = score_analysis(semantic, filler_stats, audio_features)
    summary = generate_summary(
        transcript.text,
        concept,
        semantic,
        score,
        use_gemini=use_gemini_summary,
    )

    return AnalysisResult(
        audio_path=path,
        concept=concept,
        transcript=transcript,
        filler_stats=filler_stats,
        audio_features=audio_features,
        semantic=semantic,
        sentiment=sentiment,
        score=score,
        summary=summary,
    )
