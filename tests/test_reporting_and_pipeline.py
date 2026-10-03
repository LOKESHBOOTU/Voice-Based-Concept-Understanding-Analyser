from __future__ import annotations

from pathlib import Path
from vbcua.pipeline import analyze_audio
from vbcua.reference_concepts import get_reference_concept
from vbcua.reporting import (
    create_radar_chart_png,
    create_spectrogram_png,
    create_waveform_png,
    generate_pdf_report,
)
from vbcua.storage import get_analytics_summary, save_analysis


def test_pipeline_and_pdf_generation(tmp_path):
    concept = get_reference_concept("Machine Learning")
    sample_wav = Path("samples/sample_machine_learning.wav")
    assert sample_wav.exists()

    result = analyze_audio(
        sample_wav,
        concept,
        transcript_override="Machine learning enables systems to learn from data patterns using supervised, unsupervised, and reinforcement algorithms.",
    )

    assert result.score.overall_score > 0.0
    assert result.blooms is not None
    assert result.rubric is not None
    assert result.prosody is not None
    assert len(result.viva.questions) == 3

    # Generate charts
    waveform = create_waveform_png(sample_wav)
    assert waveform is not None
    assert len(waveform) > 1000

    spectrogram = create_spectrogram_png(sample_wav)
    assert spectrogram is not None
    assert len(spectrogram) > 1000

    radar = create_radar_chart_png(result.rubric)
    assert radar is not None
    assert len(radar) > 1000

    # Generate multi-page PDF
    pdf_bytes = generate_pdf_report(result, waveform, spectrogram)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 10000  # Multi-page PDF with graphics

    # Verify storage & analytics
    test_db = tmp_path / "test_vbcua.sqlite3"
    saved = save_analysis(result, db_path=test_db, user_name="Test Student", user_email="test@edu.com")
    assert saved.record_ids.get("result_id") is not None

    analytics = get_analytics_summary(db_path=test_db)
    assert analytics["total_evaluations"] == 1
    assert analytics["avg_overall"] > 0.0
