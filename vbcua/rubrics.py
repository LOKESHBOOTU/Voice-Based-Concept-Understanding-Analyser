from __future__ import annotations

import re
from .models import AudioFeatureResult, FillerStats, ReferenceConcept, RubricScore, SemanticResult


def _clamp(val: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, val))


def evaluate_rubric(
    transcript: str,
    concept: ReferenceConcept,
    semantic: SemanticResult,
    filler_stats: FillerStats,
    audio_features: AudioFeatureResult,
    fluency_score: float,
) -> RubricScore:
    """Evaluates the explanation across 5 pedagogical dimensions for radar chart visualization."""
    text = transcript.lower()

    # 1. Conceptual Accuracy (based on semantic similarity and key term coverage)
    total_terms = len(concept.key_terms) if concept.key_terms else 1
    missing_count = len(semantic.missing_key_terms)
    term_coverage = max(0.0, (total_terms - missing_count) / total_terms)
    accuracy = _clamp((semantic.similarity_score * 0.65) + (term_coverage * 0.35))

    # 2. Technical Architecture & Mechanism (checks for structural/mechanistic language)
    mech_patterns = [
        r"\b(?:architecture|mechanism|pipeline|algorithm|process|flow|step|components|structure)\b",
        r"\b(?:layer|module|engine|framework|hardware|kernel|memory|query|interface)\b",
        r"\b(?:input|output|compute|function|protocol|data structure|model)\b",
    ]
    mech_hits = sum(1 for p in mech_patterns if re.search(p, text))
    mech_score = _clamp(0.3 + (mech_hits * 0.22) + (term_coverage * 0.2))

    # 3. Real-World Applications & Examples (checks for concrete use-case discussion)
    app_patterns = [
        r"\b(?:example|instance|such as|applied in|use case|industry|production|real-world)\b",
        r"\b(?:healthcare|finance|recommendation|autonomous|automation|e-commerce|web|cloud)\b",
        r"\b(?:deployed|practical|application|business|users)\b",
    ]
    app_hits = sum(1 for p in app_patterns if re.search(p, text))
    app_score = _clamp(0.25 + (app_hits * 0.25))

    # 4. Tradeoffs & Limitations (checks for analytical evaluation of constraints)
    tradeoff_patterns = [
        r"\b(?:limitation|tradeoff|drawback|overhead|bottleneck|constraint|challenge)\b",
        r"\b(?:latency|scalability|memory consumption|bias|overfitting|security risk)\b",
        r"\b(?:cost|complexity|maintenance|disadvantage|downside)\b",
    ]
    tradeoff_hits = sum(1 for p in tradeoff_patterns if re.search(p, text))
    tradeoff_score = _clamp(0.2 + (tradeoff_hits * 0.28))

    # 5. Delivery & Prosody (fluency, filler minimization, speaking pace)
    delivery = _clamp(fluency_score)

    return RubricScore(
        accuracy=round(accuracy, 2),
        architecture=round(mech_score, 2),
        application=round(app_score, 2),
        tradeoffs=round(tradeoff_score, 2),
        delivery=round(delivery, 2),
    )
