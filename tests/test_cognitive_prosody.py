from __future__ import annotations

from vbcua.audio_features import analyze_speech_prosody
from vbcua.knowledge_graph import extract_concept_graph
from vbcua.misconceptions import detect_misconceptions
from vbcua.models import AudioFeatureResult, FillerStats, ReferenceConcept, SemanticResult
from vbcua.rubrics import evaluate_rubric
from vbcua.viva import generate_viva_questions


def test_rubrics_evaluation():
    concept = ReferenceConcept(
        title="Machine Learning",
        text="Machine learning trains models on data.",
        key_terms=("data", "model", "training"),
    )
    semantic = SemanticResult(similarity_score=0.8, backend="test", missing_key_terms=[])
    filler = FillerStats(filler_word_count=1, total_words=50, filler_ratio=0.02, occurrences={"um": 1})
    audio = AudioFeatureResult(duration_sec=30.0, pause_ratio=0.1, rms_energy=0.06, zero_crossing_rate=0.05)

    transcript = "In machine learning, we build a pipeline model evaluated on real-world healthcare data with latency tradeoffs."
    rubric = evaluate_rubric(transcript, concept, semantic, filler, audio, fluency_score=0.85)

    assert 0.0 <= rubric.accuracy <= 1.0
    assert 0.0 <= rubric.architecture <= 1.0
    assert 0.0 <= rubric.application <= 1.0
    assert 0.0 <= rubric.tradeoffs <= 1.0
    assert 0.0 <= rubric.delivery <= 1.0
    radar = rubric.to_radar_dict()
    assert len(radar) == 5


def test_misconception_detection():
    concept = ReferenceConcept(title="Machine Learning", text="...")
    flawed_transcript = "We can use linear regression for classification of images."
    res = detect_misconceptions(flawed_transcript, concept)
    assert res.has_misconceptions is True
    assert any("Classification" in m.misconception_type for m in res.detected)

    valid_transcript = "Linear regression predicts continuous numerical prices."
    res2 = detect_misconceptions(valid_transcript, concept)
    assert len(res2.detected) == 0


def test_knowledge_graph_extraction():
    concept = ReferenceConcept(
        title="Cloud Computing",
        text="Cloud computing delivers servers and storage.",
        key_terms=("servers", "storage", "scalable"),
        subtopics=("IaaS", "PaaS"),
    )
    transcript = "Cloud computing provides scalable servers over the internet."
    kg = extract_concept_graph(transcript, concept)
    assert "servers" in kg.covered_terms
    assert "scalable" in kg.covered_terms
    assert "storage" in kg.missing_terms
    assert 0.0 < kg.coverage_ratio < 1.0


def test_viva_question_generation():
    concept = ReferenceConcept(title="Operating System", text="OS manages memory.")
    kg = extract_concept_graph("The OS manages memory.", concept)
    viva = generate_viva_questions(concept, kg, blooms=None, misconceptions=None)
    assert len(viva.questions) == 3
    assert all(q.question and q.ideal_response_hint for q in viva.questions)


def test_speech_prosody_analytics():
    transcript = "This is a smooth explanation of artificial intelligence without unnecessary hesitation."
    prosody = analyze_speech_prosody(transcript, duration_sec=5.0, pause_ratio=0.1)
    assert prosody.words_per_minute > 80.0
    assert prosody.pacing_category in (
        "Sluggish Pace (Too Slow)",
        "Optimal Conversational Pace",
        "Rushed Delivery (Too Fast)",
    )
    assert prosody.articulation_rate > 0.0
