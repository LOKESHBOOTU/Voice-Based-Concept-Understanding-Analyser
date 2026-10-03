from __future__ import annotations

from .models import (
    AudioFeatureResult,
    BloomsTaxonomyResult,
    FillerStats,
    ScoreResult,
    SemanticResult,
    SpeechProsodyResult,
)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _level(score: float) -> str:
    if score >= 0.75:
        return "Strong Understanding"
    if score >= 0.5:
        return "Moderate Understanding"
    return "Poor Understanding"


def _communication_level(fluency_score: float) -> str:
    if fluency_score >= 0.75:
        return "Confident Delivery"
    if fluency_score >= 0.5:
        return "Developing Fluency"
    return "Needs Fluency Practice"


def calculate_fluency_score(
    filler_stats: FillerStats,
    audio_features: AudioFeatureResult,
    prosody: SpeechProsodyResult | None = None,
) -> float:
    filler_penalty = _clamp(filler_stats.filler_ratio * 3.0)
    pause_penalty = _clamp(audio_features.pause_ratio)

    if audio_features.rms_energy <= 0:
        energy_score = 0.55
    else:
        energy_score = _clamp(audio_features.rms_energy / 0.08)

    fluency = 1.0 - (0.45 * filler_penalty) - (0.35 * pause_penalty)
    fluency += 0.20 * energy_score

    # Prosody adjustments (pacing & expressiveness)
    if prosody:
        if prosody.pacing_category == "Optimal Conversational Pace":
            fluency += 0.05
        elif prosody.pacing_category == "Sluggish Pace (Too Slow)":
            fluency -= 0.05

    return _clamp(fluency)


def build_feedback(
    semantic: SemanticResult,
    filler_stats: FillerStats,
    audio_features: AudioFeatureResult,
    overall_score: float,
    blooms: BloomsTaxonomyResult | None = None,
    prosody: SpeechProsodyResult | None = None,
) -> list[str]:
    feedback: list[str] = []

    if semantic.similarity_score >= 0.75:
        feedback.append("The explanation aligns well with the reference concept.")
    elif semantic.similarity_score >= 0.5:
        feedback.append("The explanation covers part of the concept but misses some depth.")
    else:
        feedback.append("The explanation needs clearer coverage of the core concept.")

    if blooms:
        feedback.append(
            f"Cognitive Depth Level: {blooms.level}. {blooms.description}"
        )

    if semantic.missing_key_terms:
        missing = ", ".join(semantic.missing_key_terms[:5])
        feedback.append(f"Important ideas to revisit: {missing}.")

    if prosody:
        feedback.append(f"Speaking Pace: {prosody.words_per_minute} WPM ({prosody.pacing_category}).")
        if "Monotone" in prosody.pitch_expressiveness:
            feedback.append("Vocal delivery is relatively flat; incorporate pitch modulation to emphasize key points.")

    if filler_stats.filler_ratio > 0.08:
        feedback.append("Frequent filler words suggest hesitation; practice shorter planned points.")
    elif filler_stats.total_words:
        feedback.append("Filler word usage is controlled.")

    if audio_features.pause_ratio > 0.35:
        feedback.append("Long silent sections indicate pauses that may reduce delivery clarity.")
    elif audio_features.duration_sec > 0:
        feedback.append("Pause balance is suitable for an explanatory answer.")

    if overall_score >= 0.75:
        feedback.append("Overall performance is ready for academic or interview review.")
    elif overall_score >= 0.5:
        feedback.append("Overall performance is promising with room for stronger examples.")
    else:
        feedback.append("Overall performance needs more concept structure and speaking practice.")

    return feedback


def score_analysis(
    semantic: SemanticResult,
    filler_stats: FillerStats,
    audio_features: AudioFeatureResult,
    blooms: BloomsTaxonomyResult | None = None,
    prosody: SpeechProsodyResult | None = None,
) -> ScoreResult:
    semantic_score = _clamp(semantic.similarity_score)
    fluency_score = calculate_fluency_score(filler_stats, audio_features, prosody)
    overall = _clamp((0.7 * semantic_score) + (0.3 * fluency_score))

    return ScoreResult(
        overall_score=overall,
        semantic_score=semantic_score,
        fluency_score=fluency_score,
        understanding_level=_level(overall),
        communication_level=_communication_level(fluency_score),
        feedback=build_feedback(
            semantic, filler_stats, audio_features, overall, blooms, prosody
        ),
    )
