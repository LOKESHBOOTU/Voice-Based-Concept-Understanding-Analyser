from __future__ import annotations

import os

from .config import GEMINI_MODEL_NAME
from .models import ReferenceConcept, ScoreResult, SemanticResult


def _heuristic_summary(
    concept: ReferenceConcept, semantic: SemanticResult, score: ScoreResult
) -> str:
    missing = ""
    if semantic.missing_key_terms:
        missing = " The response should strengthen: " + ", ".join(
            semantic.missing_key_terms[:4]
        ) + "."
    return (
        f"The explanation for {concept.title} received a "
        f"{score.understanding_level.lower()} result with an overall score of "
        f"{score.overall_score * 100:.1f}%.{missing}"
    )


def generate_summary(
    transcript: str,
    concept: ReferenceConcept,
    semantic: SemanticResult,
    score: ScoreResult,
    *,
    use_gemini: bool = False,
) -> str:
    if not use_gemini:
        return _heuristic_summary(concept, semantic, score)

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return _heuristic_summary(concept, semantic, score)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        prompt = (
            "Write a concise educational assessment summary in 3 sentences.\n"
            f"Concept: {concept.title}\n"
            f"Reference: {concept.text}\n"
            f"Transcript: {transcript[:3000]}\n"
            f"Score: {score.overall_score:.2f}\n"
            f"Level: {score.understanding_level}\n"
            f"Missing key terms: {', '.join(semantic.missing_key_terms)}"
        )
        response = model.generate_content(prompt)
        return (response.text or "").strip() or _heuristic_summary(concept, semantic, score)
    except Exception:
        return _heuristic_summary(concept, semantic, score)
