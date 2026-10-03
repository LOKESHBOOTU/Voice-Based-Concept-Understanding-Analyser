from __future__ import annotations

from vbcua.blooms_taxonomy import evaluate_blooms_taxonomy


def test_blooms_remembering_level():
    transcript = "Machine learning is defined as a branch of computer science that consists of algorithms."
    res = evaluate_blooms_taxonomy(transcript, semantic_score=0.7)
    assert res.level in ("Remembering", "Understanding")
    assert res.depth_score > 0.0


def test_blooms_analyzing_and_evaluating():
    transcript = (
        "Supervised learning differs from unsupervised learning because it uses labels. "
        "A major limitation is overfitting, which creates a tradeoff between bias and variance. "
        "We evaluate the bottleneck using cross-validation."
    )
    res = evaluate_blooms_taxonomy(transcript, semantic_score=0.85)
    assert res.level in ("Analyzing", "Evaluating")
    assert res.depth_score >= 0.7


def test_blooms_empty_transcript():
    res = evaluate_blooms_taxonomy("", semantic_score=0.0)
    assert res.level == "Remembering"
    assert res.depth_score <= 0.3
