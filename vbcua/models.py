from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReferenceConcept:
    title: str
    text: str
    key_terms: tuple[str, ...] = ()
    domain: str = "Computer Science"
    subtopics: tuple[str, ...] = ()
    expected_ontology: tuple[tuple[str, str, str], ...] = ()  # (Subject, Relation, Object)


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
class SpeechProsodyResult:
    words_per_minute: float
    pacing_category: str  # "Sluggish", "Optimal", "Rushed"
    pitch_variation_hz: float
    pitch_expressiveness: str  # "Monotone", "Balanced", "Dynamic"
    hesitation_clusters: int
    articulation_rate: float  # syllables or words per speaking sec
    warnings: list[str] = field(default_factory=list)


@dataclass
class AudioFeatureResult:
    duration_sec: float
    pause_ratio: float
    rms_energy: float
    zero_crossing_rate: float
    sample_rate: int | None = None
    prosody: SpeechProsodyResult | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class SemanticResult:
    similarity_score: float
    backend: str
    missing_key_terms: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class BloomsTaxonomyResult:
    level: str  # "Remembering", "Understanding", "Applying", "Analyzing", "Evaluating", "Creating"
    depth_score: float  # 0.0 - 1.0
    indicators: list[str]
    description: str


@dataclass
class RubricScore:
    accuracy: float
    architecture: float
    application: float
    tradeoffs: float
    delivery: float

    def to_radar_dict(self) -> dict[str, float]:
        return {
            "Conceptual Accuracy": round(self.accuracy * 100, 1),
            "Technical Architecture": round(self.architecture * 100, 1),
            "Real-World Application": round(self.application * 100, 1),
            "Tradeoffs & Edge Cases": round(self.tradeoffs * 100, 1),
            "Delivery & Prosody": round(self.delivery * 100, 1),
        }


@dataclass
class ConceptCoverageNode:
    name: str
    category: str  # "Core", "Mechanism", "Application", "Limitation"
    covered: bool
    context: str = ""


@dataclass
class KnowledgeGraphResult:
    nodes: list[ConceptCoverageNode] = field(default_factory=list)
    coverage_ratio: float = 0.0
    covered_terms: list[str] = field(default_factory=list)
    missing_terms: list[str] = field(default_factory=list)


@dataclass
class MisconceptionItem:
    detected_phrase: str
    misconception_type: str
    explanation: str
    severity: str  # "Low", "Medium", "High"


@dataclass
class MisconceptionsResult:
    detected: list[MisconceptionItem] = field(default_factory=list)
    has_misconceptions: bool = False


@dataclass
class VivaQuestion:
    question: str
    question_type: str  # "Clarification", "Deep-Dive", "Scenario"
    context_gap: str
    ideal_response_hint: str


@dataclass
class VivaResult:
    questions: list[VivaQuestion] = field(default_factory=list)


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
    blooms: BloomsTaxonomyResult | None = None
    rubric: RubricScore | None = None
    knowledge_graph: KnowledgeGraphResult | None = None
    misconceptions: MisconceptionsResult | None = None
    prosody: SpeechProsodyResult | None = None
    viva: VivaResult | None = None
    record_ids: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "audio_path": str(self.audio_path),
            "concept": {
                "title": self.concept.title,
                "text": self.concept.text,
                "key_terms": list(self.concept.key_terms),
                "domain": getattr(self.concept, "domain", "Computer Science"),
                "subtopics": list(getattr(self.concept, "subtopics", ())),
            },
            "transcript": self.transcript.__dict__,
            "filler_stats": {
                "filler_word_count": self.filler_stats.filler_word_count,
                "total_words": self.filler_stats.total_words,
                "filler_ratio": self.filler_stats.filler_ratio,
                "occurrences": dict(self.filler_stats.occurrences),
            },
            "audio_features": {
                "duration_sec": self.audio_features.duration_sec,
                "pause_ratio": self.audio_features.pause_ratio,
                "rms_energy": self.audio_features.rms_energy,
                "zero_crossing_rate": self.audio_features.zero_crossing_rate,
                "sample_rate": self.audio_features.sample_rate,
                "warnings": list(self.audio_features.warnings),
            },
            "semantic": self.semantic.__dict__,
            "sentiment": self.sentiment.__dict__,
            "score": self.score.__dict__,
            "summary": self.summary,
            "record_ids": dict(self.record_ids),
        }

        if self.blooms:
            data["blooms"] = asdict(self.blooms)
        if self.rubric:
            data["rubric"] = asdict(self.rubric)
        if self.knowledge_graph:
            data["knowledge_graph"] = {
                "nodes": [asdict(n) for n in self.knowledge_graph.nodes],
                "coverage_ratio": self.knowledge_graph.coverage_ratio,
                "covered_terms": self.knowledge_graph.covered_terms,
                "missing_terms": self.knowledge_graph.missing_terms,
            }
        if self.misconceptions:
            data["misconceptions"] = {
                "detected": [asdict(m) for m in self.misconceptions.detected],
                "has_misconceptions": self.misconceptions.has_misconceptions,
            }
        if self.prosody:
            data["prosody"] = asdict(self.prosody)
        if self.viva:
            data["viva"] = {
                "questions": [asdict(q) for q in self.viva.questions],
            }

        return data
