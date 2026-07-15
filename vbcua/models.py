from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReferenceConcept:
    title: str
    text: str
    key_terms: tuple[str, ...] = ()


@dataclass
class TranscriptionResult:
    text: str
    engine: str
    confidence: float | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class FillerStats:
    filler_word_count: int
    total_words: int
    filler_ratio: float
    occurrences: dict[str, int]


@dataclass
class AudioFeatureResult:
    duration_sec: float
    pause_ratio: float
    rms_energy: float
    zero_crossing_rate: float
    sample_rate: int | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class SemanticResult:
    similarity_score: float
    backend: str
    missing_key_terms: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class SentimentResult:
    compound_score: float
    label: str
    backend: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class ScoreResult:
    overall_score: float
    semantic_score: float
    fluency_score: float
    understanding_level: str
    communication_level: str
    feedback: list[str]


@dataclass
class AnalysisResult:
    audio_path: Path
    concept: ReferenceConcept
    transcript: TranscriptionResult
    filler_stats: FillerStats
    audio_features: AudioFeatureResult
    semantic: SemanticResult
    sentiment: SentimentResult
    score: ScoreResult
    summary: str
    record_ids: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "audio_path": str(self.audio_path),
            "concept": {
                "title": self.concept.title,
                "text": self.concept.text,
                "key_terms": list(self.concept.key_terms),
            },
            "transcript": self.transcript.__dict__,
            "filler_stats": {
                "filler_word_count": self.filler_stats.filler_word_count,
                "total_words": self.filler_stats.total_words,
                "filler_ratio": self.filler_stats.filler_ratio,
                "occurrences": dict(self.filler_stats.occurrences),
            },
            "audio_features": self.audio_features.__dict__,
            "semantic": self.semantic.__dict__,
            "sentiment": self.sentiment.__dict__,
            "score": self.score.__dict__,
            "summary": self.summary,
            "record_ids": dict(self.record_ids),
        }
