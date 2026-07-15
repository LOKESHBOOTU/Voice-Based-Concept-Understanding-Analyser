from __future__ import annotations

from io import BytesIO
from pathlib import Path
from textwrap import wrap

from .models import AnalysisResult


def create_waveform_png(audio_path: str | Path) -> bytes | None:
    try:
        import librosa
        import matplotlib.pyplot as plt
        import numpy as np

        y, sr = librosa.load(str(audio_path), sr=None, mono=True)
        times = np.arange(len(y)) / sr if sr else np.arange(len(y))
        fig, ax = plt.subplots(figsize=(9, 2.4), dpi=150)
        ax.plot(times, y, linewidth=0.7, color="#2563eb")
        ax.fill_between(times, y, 0, color="#93c5fd", alpha=0.35)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
        ax.set_title("Waveform")
        ax.grid(alpha=0.2)
        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        plt.close(fig)
        return buffer.getvalue()
    except Exception:
        return None


def _draw_wrapped_text(canvas, text: str, x: float, y: float, width_chars: int) -> float:
    for line in wrap(text, width_chars):
        canvas.drawString(x, y, line)
        y -= 13
    return y


def generate_pdf_report(result: AnalysisResult, waveform_png: bytes | None = None) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas
    except ModuleNotFoundError as exc:
        raise RuntimeError("ReportLab is required for PDF report generation.") from exc

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 48

    pdf.setTitle("VBCUA Evaluation Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(42, y, "Voice-Based Concept Understanding Analyser")
    y -= 24
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.HexColor("#334155"))
    pdf.drawString(42, y, f"Concept: {result.concept.title}")
    y -= 22

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(42, y, "Evaluation Metrics")
    y -= 18
    pdf.setFont("Helvetica", 10)

    metrics = [
        ("Overall Score", f"{result.score.overall_score * 100:.1f}%"),
        ("Semantic Similarity", f"{result.semantic.similarity_score * 100:.1f}%"),
        ("Fluency Score", f"{result.score.fluency_score * 100:.1f}%"),
        ("Understanding Level", result.score.understanding_level),
        ("Communication Level", result.score.communication_level),
        ("Filler Words", str(result.filler_stats.filler_word_count)),
        ("Filler Ratio", f"{result.filler_stats.filler_ratio * 100:.1f}%"),
        ("Pause Ratio", f"{result.audio_features.pause_ratio * 100:.1f}%"),
        ("RMS Energy", f"{result.audio_features.rms_energy:.4f}"),
        ("Sentiment", result.sentiment.label),
    ]

    for index, (label, value) in enumerate(metrics):
        x = 42 if index % 2 == 0 else 300
        if index % 2 == 0 and index:
            y -= 16
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(x, y, f"{label}:")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(x + 105, y, value)
    y -= 32

    if waveform_png:
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(42, y, "Waveform")
        y -= 128
        pdf.drawImage(
            ImageReader(BytesIO(waveform_png)),
            42,
            y,
            width=500,
            height=110,
            preserveAspectRatio=True,
            mask="auto",
        )
        y -= 24

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(42, y, "AI Summary")
    y -= 16
    pdf.setFont("Helvetica", 9)
    y = _draw_wrapped_text(pdf, result.summary, 42, y, 96) - 10

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(42, y, "Feedback")
    y -= 16
    pdf.setFont("Helvetica", 9)
    for item in result.score.feedback:
        y = _draw_wrapped_text(pdf, f"- {item}", 42, y, 96)
    y -= 8

    if y < 170:
        pdf.showPage()
        y = height - 48

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(42, y, "Transcript")
    y -= 16
    pdf.setFont("Helvetica", 9)
    transcript = result.transcript.text or "No transcript was produced."
    for paragraph in transcript.splitlines() or [transcript]:
        for line in wrap(paragraph, 96):
            if y < 48:
                pdf.showPage()
                y = height - 48
                pdf.setFont("Helvetica", 9)
            pdf.drawString(42, y, line)
            y -= 12

    pdf.save()
    return buffer.getvalue()
