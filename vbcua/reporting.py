from __future__ import annotations

from io import BytesIO
from pathlib import Path
from textwrap import wrap

from .models import AnalysisResult, RubricScore
from .audio_features import create_spectrogram_png


def create_waveform_png(audio_path: str | Path) -> bytes | None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        import wave

        path = Path(audio_path)
        with wave.open(str(path), "rb") as wf:
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())
            channels = wf.getnchannels()

        dtype = np.int16 if sample_width == 2 else (np.uint8 if sample_width == 1 else np.int32)
        audio = np.frombuffer(frames, dtype=dtype).astype(np.float32)
        if sample_width == 1:
            audio -= 128
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)

        max_val = np.max(np.abs(audio)) or 1.0
        y = audio / max_val
        times = np.arange(len(y)) / sample_rate if sample_rate else np.arange(len(y))

        fig, ax = plt.subplots(figsize=(9, 2.2), dpi=150)
        ax.plot(times, y, linewidth=0.7, color="#1d4ed8")
        ax.fill_between(times, y, 0, color="#93c5fd", alpha=0.35)
        ax.set_xlabel("Time (s)", fontsize=8)
        ax.set_ylabel("Amplitude", fontsize=8)
        ax.set_title("Speech Amplitude Waveform", fontsize=9, pad=4)
        ax.grid(alpha=0.2)
        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        plt.close(fig)
        return buffer.getvalue()
    except Exception:
        return None


def create_radar_chart_png(rubric: RubricScore) -> bytes | None:
    """Generates a 5-axis Radar / Spider chart for the pedagogical evaluation dimensions."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        categories = [
            "Conceptual\nAccuracy",
            "Technical\nArchitecture",
            "Real-World\nApplication",
            "Tradeoffs &\nLimitations",
            "Delivery &\nProsody",
        ]
        values = [
            rubric.accuracy * 100,
            rubric.architecture * 100,
            rubric.application * 100,
            rubric.tradeoffs * 100,
            rubric.delivery * 100,
        ]

        # Close the loop
        values += values[:1]
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(3.8, 3.8), subplot_kw=dict(polar=True), dpi=150)
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#f8fafc")

        # Draw plot
        ax.plot(angles, values, color="#2563eb", linewidth=2.0, linestyle="solid")
        ax.fill(angles, values, color="#3b82f6", alpha=0.3)

        # Labels & Ticks
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=7.5, color="#1e293b", weight="bold")
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=6.5, color="#64748b")
        ax.grid(color="#cbd5e1", linestyle="--", linewidth=0.6)

        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight")
        plt.close(fig)
        return buffer.getvalue()
    except Exception:
        return None


def _draw_wrapped_text(canvas, text: str, x: float, y: float, width_chars: int) -> float:
    for line in wrap(text, width_chars):
        canvas.drawString(x, y, line)
        y -= 13
    return y


def generate_pdf_report(
    result: AnalysisResult,
    waveform_png: bytes | None = None,
    spectrogram_png: bytes | None = None,
) -> bytes:
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

    # ---------------- PAGE 1: EXECUTIVE ASSESSMENT SUMMARY ----------------
    y = height - 42

    # Header Banner
    pdf.setFillColor(colors.HexColor("#1e3a8a"))
    pdf.rect(36, y - 48, width - 72, 54, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(48, y - 20, "VOICE-BASED CONCEPT UNDERSTANDING ANALYSER")
    pdf.setFont("Helvetica", 9.5)
    pdf.drawString(48, y - 36, "Major Project Assessment Report  |  Multimodal Cognitive & Speech Intelligence")

    y -= 74

    # Concept Metadata
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 13)
    domain = getattr(result.concept, "domain", "General")
    pdf.drawString(42, y, f"Topic: {result.concept.title}")
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.HexColor("#2563eb"))
    pdf.drawRightString(width - 42, y, f"Domain: {domain}")

    y -= 22

    # Executive Scorecard Box
    pdf.setFillColor(colors.HexColor("#f1f5f9"))
    pdf.roundRect(42, y - 62, width - 84, 62, 4, fill=1, stroke=0)

    # 4 Scorecard Columns
    col_w = (width - 84) / 4
    cards = [
        ("Overall Score", f"{result.score.overall_score * 100:.1f}%", colors.HexColor("#1d4ed8")),
        ("Cognitive Depth", result.blooms.level if result.blooms else "Understanding", colors.HexColor("#7c3aed")),
        ("Understanding", result.score.understanding_level, colors.HexColor("#059669")),
        ("Communication", result.score.communication_level, colors.HexColor("#d97706")),
    ]

    for i, (title, val, val_col) in enumerate(cards):
        cx = 42 + (i * col_w) + 12
        pdf.setFillColor(colors.HexColor("#475569"))
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(cx, y - 20, title.upper())
        pdf.setFillColor(val_col)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(cx, y - 40, val)

    y -= 84

    # Radar Chart & 5 Rubric Metrics (Side-by-side)
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(42, y, "Pedagogical Multi-Criteria Rubric Breakdown")
    y -= 16

    rubric_png = None
    if result.rubric:
        rubric_png = create_radar_chart_png(result.rubric)

    if rubric_png:
        # Draw radar chart on right
        pdf.drawImage(
            ImageReader(BytesIO(rubric_png)),
            width - 235,
            y - 165,
            width=180,
            height=180,
            preserveAspectRatio=True,
            mask="auto",
        )

    # Draw rubric items on left
    rubric_vals = [
        ("Conceptual Accuracy", f"{result.rubric.accuracy * 100:.0f}%" if result.rubric else "N/A"),
        ("Technical Architecture", f"{result.rubric.architecture * 100:.0f}%" if result.rubric else "N/A"),
        ("Real-World Application", f"{result.rubric.application * 100:.0f}%" if result.rubric else "N/A"),
        ("Tradeoffs & Edge Cases", f"{result.rubric.tradeoffs * 100:.0f}%" if result.rubric else "N/A"),
        ("Delivery & Prosody", f"{result.rubric.delivery * 100:.0f}%" if result.rubric else "N/A"),
    ]

    ry = y
    for label, score_str in rubric_vals:
        pdf.setFillColor(colors.HexColor("#334155"))
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(42, ry - 14, label)
        pdf.setFont("Helvetica-Bold", 9.5)
        pdf.setFillColor(colors.HexColor("#2563eb"))
        pdf.drawString(220, ry - 14, score_str)
        ry -= 24

    y -= 175

    # Speech Prosody Overview
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(42, y, "Speech Prosody & Delivery Analytics")
    y -= 18

    prosody_metrics = [
        ("Speaking Rate", f"{result.prosody.words_per_minute} WPM ({result.prosody.pacing_category})" if result.prosody else f"{len(result.transcript.text.split())} words"),
        ("Pitch Cadence", result.prosody.pitch_expressiveness if result.prosody else "Balanced"),
        ("Pause Ratio", f"{result.audio_features.pause_ratio * 100:.1f}% of explanation"),
        ("Filler Words", f"{result.filler_stats.filler_word_count} occurrences ({result.filler_stats.filler_ratio * 100:.1f}%)"),
    ]

    for i, (label, val) in enumerate(prosody_metrics):
        px = 42 if i % 2 == 0 else 300
        if i % 2 == 0 and i > 0:
            y -= 18
        pdf.setFont("Helvetica-Bold", 8.5)
        pdf.setFillColor(colors.HexColor("#475569"))
        pdf.drawString(px, y, f"{label}:")
        pdf.setFont("Helvetica", 8.5)
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.drawString(px + 90, y, str(val))

    y -= 36

    # Qualitative Feedback & Recommendations
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(42, y, "Evaluator Feedback & Educational Recommendations")
    y -= 16
    pdf.setFont("Helvetica", 8.5)
    pdf.setFillColor(colors.HexColor("#334155"))
    for item in result.score.feedback[:5]:
        y = _draw_wrapped_text(pdf, f"- {item}", 42, y, 92)

    # ---------------- PAGE 2: COGNITIVE MAPPING & VIVA-VOCE ----------------
    pdf.showPage()
    y = height - 42

    pdf.setFillColor(colors.HexColor("#1e3a8a"))
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(42, y, "Concept Ontology & Adaptive Viva-Voce Examination")
    y -= 24

    # Knowledge Graph Coverage
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.drawString(42, y, "Concept Ontology Coverage")
    y -= 16

    if result.knowledge_graph:
        pdf.setFont("Helvetica", 8.5)
        cov_pct = f"{result.knowledge_graph.coverage_ratio * 100:.0f}%"
        pdf.setFillColor(colors.HexColor("#059669"))
        pdf.drawString(42, y, f"Ontology Coverage: {cov_pct}")
        y -= 14

        pdf.setFillColor(colors.HexColor("#334155"))
        covered_str = ", ".join(result.knowledge_graph.covered_terms) or "None identified"
        missing_str = ", ".join(result.knowledge_graph.missing_terms) or "None (Full coverage)"
        y = _draw_wrapped_text(pdf, f"Demonstrated Concepts: {covered_str}", 42, y, 92) - 4
        y = _draw_wrapped_text(pdf, f"Omitted Concepts: {missing_str}", 42, y, 92) - 10

    # Misconceptions Section (if any detected)
    if result.misconceptions and result.misconceptions.has_misconceptions:
        pdf.setFillColor(colors.HexColor("#b91c1c"))
        pdf.setFont("Helvetica-Bold", 10.5)
        pdf.drawString(42, y, "Detected Factual Misconceptions & Corrections")
        y -= 16
        for m in result.misconceptions.detected:
            pdf.setFillColor(colors.HexColor("#991b1b"))
            pdf.setFont("Helvetica-Bold", 8.5)
            y = _draw_wrapped_text(pdf, f"[!] {m.misconception_type} (Phrase: '{m.detected_phrase}')", 42, y, 90)
            pdf.setFont("Helvetica", 8.5)
            pdf.setFillColor(colors.HexColor("#475569"))
            y = _draw_wrapped_text(pdf, f"    Correction: {m.explanation}", 42, y, 90) - 6
        y -= 6

    # Adaptive Viva-Voce Questions
    if result.viva and result.viva.questions:
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.setFont("Helvetica-Bold", 10.5)
        pdf.drawString(42, y, "Adaptive Viva-Voce Oral Examiner Questions")
        y -= 16
        for idx, q in enumerate(result.viva.questions, 1):
            pdf.setFillColor(colors.HexColor("#1d4ed8"))
            pdf.setFont("Helvetica-Bold", 8.5)
            pdf.drawString(42, y, f"Q{idx} [{q.question_type}]:")
            pdf.setFillColor(colors.HexColor("#1e293b"))
            pdf.setFont("Helvetica", 8.5)
            y = _draw_wrapped_text(pdf, q.question, 140, y, 76)
            pdf.setFillColor(colors.HexColor("#64748b"))
            pdf.setFont("Helvetica-Oblique", 7.5)
            y = _draw_wrapped_text(pdf, f"Hint: {q.ideal_response_hint}", 140, y, 76) - 6

    # Waveform Visualizer
    if waveform_png:
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(42, y, "Speech Waveform")
        y -= 85
        pdf.drawImage(
            ImageReader(BytesIO(waveform_png)),
            42,
            y,
            width=510,
            height=75,
            preserveAspectRatio=True,
            mask="auto",
        )
        y -= 18

    # ---------------- PAGE 3: TRANSCRIPT & VERIFICATION ----------------
    pdf.showPage()
    y = height - 42

    pdf.setFillColor(colors.HexColor("#1e3a8a"))
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(42, y, "Full Verbatim Transcript & Assessment Audit")
    y -= 22

    pdf.setFont("Helvetica-Bold", 9)
    pdf.setFillColor(colors.HexColor("#475569"))
    pdf.drawString(42, y, f"Engine: {result.transcript.engine}   |   Audio Duration: {result.audio_features.duration_sec:.1f}s   |   Sample Rate: {result.audio_features.sample_rate or 16000} Hz")
    y -= 18

    pdf.setFont("Helvetica", 8.5)
    pdf.setFillColor(colors.HexColor("#1e293b"))
    transcript = result.transcript.text or "No spoken transcript recorded."
    for paragraph in transcript.splitlines() or [transcript]:
        for line in wrap(paragraph, 94):
            if y < 48:
                pdf.showPage()
                y = height - 42
                pdf.setFont("Helvetica", 8.5)
            pdf.drawString(42, y, line)
            y -= 12

    # Footer Watermark
    pdf.setFont("Helvetica", 7.5)
    pdf.setFillColor(colors.HexColor("#94a3b8"))
    pdf.drawString(42, 30, "Generated by Voice-Based Concept Understanding Analyser (VBCUA) - AI-Assisted Oral Examination System")

    pdf.save()
    return buffer.getvalue()
