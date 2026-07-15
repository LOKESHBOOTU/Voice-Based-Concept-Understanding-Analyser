from vbcua.models import AudioFeatureResult, FillerStats, SemanticResult
from vbcua.scoring import calculate_fluency_score, score_analysis


def test_fluency_score_penalizes_many_fillers_and_pauses():
    clean = calculate_fluency_score(
        FillerStats(0, 100, 0.0, {}),
        AudioFeatureResult(30.0, 0.05, 0.05, 0.02),
    )
    hesitant = calculate_fluency_score(
        FillerStats(20, 100, 0.2, {"um": 10, "like": 10}),
        AudioFeatureResult(30.0, 0.55, 0.01, 0.02),
    )

    assert clean > hesitant
    assert 0 <= hesitant <= 1


def test_score_analysis_produces_expected_understanding_level():
    result = score_analysis(
        SemanticResult(0.82, "test"),
        FillerStats(1, 120, 1 / 120, {"um": 1}),
        AudioFeatureResult(45.0, 0.1, 0.05, 0.03),
    )

    assert result.understanding_level == "Strong Understanding"
    assert result.overall_score >= 0.75
