from __future__ import annotations

from .models import SentimentResult
from .semantic import tokenize

POSITIVE_WORDS = {
    "clear",
    "confident",
    "accurate",
    "strong",
    "useful",
    "good",
    "improve",
    "effective",
    "correct",
    "understand",
    "learning",
}

NEGATIVE_WORDS = {
    "confused",
    "wrong",
    "bad",
    "difficult",
    "unclear",
    "poor",
    "problem",
    "error",
    "mistake",
    "hesitate",
    "hesitation",
}


def _label(compound: float) -> str:
    if compound >= 0.2:
        return "Positive"
    if compound <= -0.2:
        return "Negative"
    return "Neutral"


def _fallback_sentiment(transcript: str) -> SentimentResult:
    tokens = tokenize(transcript)
    if not tokens:
        return SentimentResult(0.0, "Neutral", "lexicon fallback")

    positive = sum(1 for token in tokens if token in POSITIVE_WORDS)
    negative = sum(1 for token in tokens if token in NEGATIVE_WORDS)
    compound = (positive - negative) / max(1, positive + negative + 2)
    return SentimentResult(compound, _label(compound), "lexicon fallback")


def analyze_sentiment(transcript: str) -> SentimentResult:
    try:
        from nltk.sentiment import SentimentIntensityAnalyzer

        analyzer = SentimentIntensityAnalyzer()
        compound = float(analyzer.polarity_scores(transcript).get("compound", 0.0))
        return SentimentResult(compound, _label(compound), "nltk vader")
    except ModuleNotFoundError:
        return _fallback_sentiment(transcript)
    except Exception as exc:
        result = _fallback_sentiment(transcript)
        result.warnings.append(f"NLTK sentiment unavailable; used fallback: {exc}")
        return result
