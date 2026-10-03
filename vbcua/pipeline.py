from __future__ import annotations

from pathlib import Path

from .audio_features import analyze_filler_words, extract_audio_features
from .blooms_taxonomy import evaluate_blooms_taxonomy
from .knowledge_graph import extract_concept_graph
from .misconceptions import detect_misconceptions
from .models import AnalysisResult, ReferenceConcept
from .rubrics import evaluate_rubric
from .scoring import calculate_fluency_score, score_analysis
from .semantic import evaluate_semantic_understanding
from .summary import generate_summary
from .text_analysis import analyze_sentiment
from .transcription import transcribe_audio
from .viva import generate_viva_questions


def analyze_audio(
    audio_path: str | Path,
    concept: ReferenceConcept,
    *,
    transcript_override: str | None = None,
    use_gemini_summary: bool = False,
) -> AnalysisResult:
    """Orchestrates end-to-end multimodal analysis: transcription, acoustics, cognitive depth, rubrics, and viva-voce."""
    path = Path(audio_path)
    transcript = transcribe_audio(path, transcript_override=transcript_override)
    filler_stats = analyze_filler_words(transcript.text)
    audio_features = extract_audio_features(path, transcript=transcript.text)
    prosody = audio_features.prosody

    semantic = evaluate_semantic_understanding(transcript.text, concept)
    sentiment = analyze_sentiment(transcript.text)

    # Major Project Cognitive AI extensions
    blooms = evaluate_blooms_taxonomy(transcript.text, semantic.similarity_score)
    misconceptions = detect_misconceptions(transcript.text, concept)
    knowledge_graph = extract_concept_graph(transcript.text, concept)

    fluency_score = calculate_fluency_score(filler_stats, audio_features, prosody)
    rubric = evaluate_rubric(
        transcript.text,
        concept,
        semantic,
        filler_stats,
        audio_features,
        fluency_score,
    )

    viva = generate_viva_questions(concept, knowledge_graph, blooms, misconceptions)

    score = score_analysis(
        semantic,
        filler_stats,
        audio_features,
        blooms=blooms,
        prosody=prosody,
    )

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
        blooms=blooms,
        rubric=rubric,
        knowledge_graph=knowledge_graph,
        misconceptions=misconceptions,
        prosody=prosody,
        viva=viva,
    )
