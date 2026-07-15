from __future__ import annotations

import time
from pathlib import Path

import streamlit as st

from vbcua.config import REPORT_DIR, UPLOAD_DIR, ensure_runtime_dirs
from vbcua.models import ReferenceConcept
from vbcua.pipeline import analyze_audio
from vbcua.reference_concepts import DEFAULT_CONCEPTS, concept_titles, get_reference_concept
from vbcua.reporting import create_waveform_png, generate_pdf_report
from vbcua.storage import init_db, recent_results, save_analysis, save_report_record


st.set_page_config(
    page_title="VBCUA",
    page_icon=":microphone:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_metric_card(label: str, value: str, caption: str | None = None) -> None:
    st.metric(label, value)
    if caption:
        st.caption(caption)


def save_uploaded_audio(uploaded_file) -> Path:
    ensure_runtime_dirs()
    suffix = Path(uploaded_file.name).suffix or ".wav"
    safe_name = f"{int(time.time())}_{Path(uploaded_file.name).stem}{suffix}"
    audio_path = UPLOAD_DIR / safe_name
    audio_path.write_bytes(uploaded_file.getbuffer())
    return audio_path


def resolve_concept(
    selected_title: str, custom_title: str, custom_reference: str, custom_terms: str
) -> ReferenceConcept:
    if selected_title == "Custom Concept":
        terms = tuple(term.strip() for term in custom_terms.split(",") if term.strip())
        return ReferenceConcept(
            title=custom_title.strip() or "Custom Concept",
            text=custom_reference.strip(),
            key_terms=terms,
        )
    return get_reference_concept(selected_title)


def render_recent_results() -> None:
    rows = recent_results(limit=8)
    if not rows:
        st.caption("No saved evaluations yet.")
        return

    st.dataframe(
        [
            {
                "Result": row["result_id"],
                "Concept": row["concept_title"],
                "Overall": percent(row["overall_score"]),
                "Understanding": row["understanding_level"],
                "Communication": row["communication_level"],
                "Sentiment": row["sentiment_label"],
                "Created": row["created_at"],
            }
            for row in rows
        ],
        use_container_width=True,
        hide_index=True,
    )


ensure_runtime_dirs()
init_db()

st.title("Voice-Based Concept Understanding Analyser")

with st.sidebar:
    st.header("Assessment")
    selected = st.selectbox(
        "Reference concept",
        options=concept_titles() + ["Custom Concept"],
        index=0,
    )

    custom_title = ""
    custom_reference = ""
    custom_terms = ""
    if selected == "Custom Concept":
        custom_title = st.text_input("Concept title", value="Custom Concept")
        custom_reference = st.text_area("Reference explanation", height=180)
        custom_terms = st.text_input("Key terms", placeholder="term one, term two")
    else:
        concept = get_reference_concept(selected)
        st.text_area("Reference explanation", value=concept.text, height=190, disabled=True)
        st.caption("Key terms: " + ", ".join(concept.key_terms))

    st.divider()
    st.header("Learner")
    learner_name = st.text_input("Name")
    learner_email = st.text_input("Email")
    learner_role = st.selectbox("Role", ["student", "educator", "trainer", "researcher"])
    use_gemini = st.toggle("Gemini summary", value=False)

main_col, history_col = st.columns([2.2, 1], gap="large")

with main_col:
    uploaded_audio = st.file_uploader(
        "Audio explanation",
        type=["wav", "mp3", "m4a", "flac", "ogg"],
    )
    transcript_override = st.text_area(
        "Manual transcript",
        placeholder="Optional transcript for offline testing or when Whisper is unavailable.",
        height=120,
    )

    if uploaded_audio:
        st.audio(uploaded_audio)

    analyze_clicked = st.button(
        "Analyze Explanation",
        type="primary",
        use_container_width=True,
        disabled=uploaded_audio is None,
    )

with history_col:
    st.subheader("Recent Results")
    render_recent_results()

if analyze_clicked and uploaded_audio:
    selected_concept = resolve_concept(selected, custom_title, custom_reference, custom_terms)
    if not selected_concept.text.strip():
        st.error("A reference explanation is required for custom concepts.")
        st.stop()

    audio_path = save_uploaded_audio(uploaded_audio)

    with st.spinner("Evaluating transcript, semantics, and speech features..."):
        analysis = analyze_audio(
            audio_path,
            selected_concept,
            transcript_override=transcript_override,
            use_gemini_summary=use_gemini,
        )
        analysis = save_analysis(
            analysis,
            user_name=learner_name or None,
            user_email=learner_email or None,
            role=learner_role,
        )
        waveform_png = create_waveform_png(audio_path)
        pdf_bytes = generate_pdf_report(analysis, waveform_png)
        report_name = f"vbcua_report_{analysis.record_ids.get('result_id', int(time.time()))}.pdf"
        report_path = REPORT_DIR / report_name
        report_path.write_bytes(pdf_bytes)
        if analysis.record_ids.get("result_id"):
            save_report_record(
                int(analysis.record_ids["result_id"]),
                report_path,
                max(1, len(pdf_bytes) // 1024),
            )

    st.success(f"Evaluation complete: {analysis.score.understanding_level}")

    score_cols = st.columns(4)
    with score_cols[0]:
        render_metric_card("Overall", percent(analysis.score.overall_score))
    with score_cols[1]:
        render_metric_card("Semantic", percent(analysis.semantic.similarity_score))
    with score_cols[2]:
        render_metric_card("Fluency", percent(analysis.score.fluency_score))
    with score_cols[3]:
        render_metric_card("Pause Ratio", percent(analysis.audio_features.pause_ratio))
    st.caption(
        f"Communication: {analysis.score.communication_level} | "
        f"Sentiment: {analysis.sentiment.label} ({analysis.sentiment.compound_score:.2f})"
    )

    tabs = st.tabs(["Review", "Transcript", "Audio Metrics", "Report"])
    with tabs[0]:
        st.subheader(analysis.score.understanding_level)
        st.write(analysis.summary)
        for feedback_item in analysis.score.feedback:
            st.markdown(f"- {feedback_item}")
        if analysis.semantic.warnings or analysis.transcript.warnings or analysis.audio_features.warnings:
            st.warning(
                "\n".join(
                    analysis.semantic.warnings
                    + analysis.transcript.warnings
                    + analysis.audio_features.warnings
                    + analysis.sentiment.warnings
                )
            )

    with tabs[1]:
        st.text_area("Transcribed explanation", value=analysis.transcript.text, height=240)
        st.caption(f"Transcription engine: {analysis.transcript.engine}")

    with tabs[2]:
        if waveform_png:
            st.image(waveform_png, caption="Waveform", use_container_width=True)
        metric_rows = {
            "Duration (sec)": round(analysis.audio_features.duration_sec, 2),
            "RMS energy": round(analysis.audio_features.rms_energy, 5),
            "Zero crossing rate": round(analysis.audio_features.zero_crossing_rate, 5),
            "Filler words": analysis.filler_stats.filler_word_count,
            "Total words": analysis.filler_stats.total_words,
            "Filler ratio": percent(analysis.filler_stats.filler_ratio),
            "Sentiment": analysis.sentiment.label,
            "Sentiment score": round(analysis.sentiment.compound_score, 3),
            "Semantic backend": analysis.semantic.backend,
        }
        st.json(metric_rows)
        if analysis.filler_stats.occurrences:
            st.bar_chart(analysis.filler_stats.occurrences)

    with tabs[3]:
        st.download_button(
            "Download PDF Report",
            data=pdf_bytes,
            file_name=report_name,
            mime="application/pdf",
            use_container_width=True,
        )
        st.caption(str(report_path))
