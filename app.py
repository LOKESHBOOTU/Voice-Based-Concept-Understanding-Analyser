from __future__ import annotations

import io
import time
from pathlib import Path

import streamlit as st

from vbcua.audio_features import create_spectrogram_png
from vbcua.config import BASE_DIR, REPORT_DIR, UPLOAD_DIR, ensure_runtime_dirs
from vbcua.models import ReferenceConcept
from vbcua.pipeline import analyze_audio
from vbcua.reference_concepts import (
    DEFAULT_CONCEPTS,
    concept_domains,
    concept_titles,
    concepts_by_domain,
    get_reference_concept,
)
from vbcua.reporting import (
    create_radar_chart_png,
    create_waveform_png,
    generate_pdf_report,
)
from vbcua.storage import (
    get_analytics_summary,
    init_db,
    recent_results,
    save_analysis,
    save_report_record,
)


st.set_page_config(
    page_title="VBCUA 2.0 • Major Project",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling and readability
st.markdown(
    """
    <style>
    .metric-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 2px;
    }
    .badge-covered {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }
    .badge-missing {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def save_audio_bytes(audio_bytes: bytes, filename: str) -> Path:
    ensure_runtime_dirs()
    suffix = Path(filename).suffix or ".wav"
    safe_name = f"{int(time.time())}_{Path(filename).stem}{suffix}"
    audio_path = UPLOAD_DIR / safe_name
    audio_path.write_bytes(audio_bytes)
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
            domain="Custom Domain",
        )
    return get_reference_concept(selected_title)


ensure_runtime_dirs()
init_db()

# Initialize session state variables
if "recorder_id" not in st.session_state:
    st.session_state.recorder_id = 0
if "current_analysis" not in st.session_state:
    st.session_state.current_analysis = None
if "waveform_png" not in st.session_state:
    st.session_state.waveform_png = None
if "spectrogram_png" not in st.session_state:
    st.session_state.spectrogram_png = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
if "report_name" not in st.session_state:
    st.session_state.report_name = ""
if "report_path" not in st.session_state:
    st.session_state.report_path = ""

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("### 🎙️ VBCUA 2.0")
    st.caption("**Voice-Based Concept Understanding Analyser**\n*Major Project Edition*")
    st.divider()

    st.markdown("#### 📚 Assessment Concept")
    domain_filter = st.selectbox(
        "Curriculum Domain",
        options=["All Domains"] + concept_domains() + ["Custom Concept"],
        index=0,
    )

    if domain_filter == "Custom Concept":
        selected = "Custom Concept"
    elif domain_filter == "All Domains":
        selected = st.selectbox("Select Topic", options=concept_titles(), index=0)
    else:
        domain_topics = [c.title for c in concepts_by_domain(domain_filter)]
        selected = st.selectbox("Select Topic", options=domain_topics, index=0)

    custom_title = ""
    custom_reference = ""
    custom_terms = ""

    if selected == "Custom Concept":
        custom_title = st.text_input("Concept Title", value="Custom Concept")
        custom_reference = st.text_area("Reference Explanation", height=160)
        custom_terms = st.text_input("Key Terms (comma-separated)", placeholder="term1, term2, term3")
    else:
        concept_obj = get_reference_concept(selected)
        with st.expander("📖 View Reference Overview", expanded=False):
            st.markdown(f"**Domain:** {getattr(concept_obj, 'domain', 'Computer Science')}")
            st.write(concept_obj.text)
            st.markdown(
                "**Key Terms:** "
                + ", ".join([f"`{t}`" for t in concept_obj.key_terms])
            )
            if getattr(concept_obj, "subtopics", None):
                st.markdown(
                    "**Subtopics:** "
                    + ", ".join([f"`{s}`" for s in concept_obj.subtopics])
                )

    st.divider()
    st.markdown("#### 👤 Candidate Profile")
    learner_name = st.text_input("Candidate Name", placeholder="e.g. Jane Doe")
    learner_email = st.text_input("Email", placeholder="e.g. jane@university.edu")
    learner_role = st.selectbox("Role", ["student", "educator", "candidate", "researcher"])
    use_gemini = st.toggle("AI Executive Summary (Gemini)", value=False)

    st.divider()
    # Global analytics quick glance
    analytics = get_analytics_summary()
    st.markdown("#### 📊 System Stats")
    st.caption(f"Evaluations Recorded: **{analytics.get('total_evaluations', 0)}**")
    if analytics.get("total_evaluations", 0) > 0:
        st.caption(f"Cohort Avg Score: **{analytics.get('avg_overall', 0)}%**")
        st.caption(f"Avg Speaking Pace: **{analytics.get('avg_wpm', 0)} WPM**")

# ----------------- MAIN INTERFACE -----------------
st.title("🎙️ Voice-Based Concept Understanding Analyser")
st.markdown(
    "**Major Project Assessment Studio:** Evaluate conceptual mastery, speech prosody, "
    "Bloom's cognitive depth, and engage with an adaptive AI Viva-Voce oral examiner."
)

st.write("")

# ---------------- AUDIO INGESTION LAYER ----------------
st.subheader("1. Audio Explanation Input")
input_mode = st.radio(
    "Choose Input Method:",
    options=["🎙️ Direct Microphone Recording", "📁 Upload Audio File", "🎵 Preset Sample Audio"],
    horizontal=True,
)

audio_file_path: Path | None = None
active_audio_bytes: bytes | None = None

if input_mode == "🎙️ Direct Microphone Recording":
    st.info("Click the microphone below to record your conceptual explanation directly in the browser.")

    mic_cols = st.columns([3, 1], gap="medium")
    with mic_cols[0]:
        recorded_audio = st.audio_input(
            "Record Spoken Explanation",
            key=f"mic_recorder_{st.session_state.recorder_id}",
        )
    with mic_cols[1]:
        st.write("")
        st.write("")
        if st.button("🔄 Reset / Re-record", use_container_width=True, help="Clear and restart microphone recording"):
            st.session_state.recorder_id += 1
            st.session_state.current_analysis = None
            st.rerun()

    if recorded_audio:
        active_audio_bytes = recorded_audio.getvalue()
        audio_file_path = save_audio_bytes(active_audio_bytes, "mic_recording.wav")
        
        play_cols = st.columns([3, 1], gap="medium")
        with play_cols[0]:
            st.audio(active_audio_bytes)
        with play_cols[1]:
            st.write("")
            if st.button("🗑️ Discard Recording", type="secondary", use_container_width=True):
                st.session_state.recorder_id += 1
                st.session_state.current_analysis = None
                st.rerun()

elif input_mode == "📁 Upload Audio File":
    uploaded_file = st.file_uploader(
        "Upload audio explanation (WAV, MP3, M4A, OGG, FLAC)",
        type=["wav", "mp3", "m4a", "flac", "ogg"],
    )
    if uploaded_file:
        active_audio_bytes = uploaded_file.getvalue()
        audio_file_path = save_audio_bytes(active_audio_bytes, uploaded_file.name)
        st.audio(active_audio_bytes)

elif input_mode == "🎵 Preset Sample Audio":
    preset_path = BASE_DIR / "samples" / "sample_machine_learning.wav"
    if preset_path.exists():
        active_audio_bytes = preset_path.read_bytes()
        audio_file_path = preset_path
        st.success("Loaded preset sample: `Machine Learning explanation` (WAV audio)")
        st.audio(active_audio_bytes)
    else:
        st.warning("Preset sample audio not found on disk.")

with st.expander("⚙️ Manual Transcript / Offline Testing (Optional)"):
    transcript_override = st.text_area(
        "Manual Transcript Override",
        placeholder="Provide or edit the transcript manually if Whisper is offline or for rapid testing.",
        height=90,
    )

st.write("")

action_cols = st.columns([3, 1], gap="medium")
with action_cols[0]:
    analyze_clicked = st.button(
        "🚀 Run Multimodal Evaluation",
        type="primary",
        use_container_width=True,
        disabled=audio_file_path is None,
    )
with action_cols[1]:
    if st.session_state.current_analysis is not None:
        if st.button("🔄 Start New Assessment", use_container_width=True):
            st.session_state.current_analysis = None
            st.session_state.recorder_id += 1
            st.rerun()

# ---------------- EVALUATION & DASHBOARD EXECUTION ----------------
if analyze_clicked and audio_file_path:
    selected_concept = resolve_concept(selected, custom_title, custom_reference, custom_terms)
    if not selected_concept.text.strip():
        st.error("A reference explanation is required for custom concepts.")
        st.stop()

    with st.spinner("Analyzing Speech Acoustics, Semantic Similarity, Bloom's Taxonomy, and Viva Gaps..."):
        analysis = analyze_audio(
            audio_file_path,
            selected_concept,
            transcript_override=transcript_override or None,
            use_gemini_summary=use_gemini,
        )
        analysis = save_analysis(
            analysis,
            user_name=learner_name or None,
            user_email=learner_email or None,
            role=learner_role,
        )

        waveform_png = create_waveform_png(audio_file_path)
        spectrogram_png = create_spectrogram_png(audio_file_path)
        pdf_bytes = generate_pdf_report(analysis, waveform_png, spectrogram_png)

        report_id = analysis.record_ids.get("result_id", int(time.time()))
        report_name = f"vbcua_report_{report_id}.pdf"
        report_path = REPORT_DIR / report_name
        report_path.write_bytes(pdf_bytes)

        if analysis.record_ids.get("result_id"):
            save_report_record(
                int(analysis.record_ids["result_id"]),
                report_path,
                max(1, len(pdf_bytes) // 1024),
            )

        # Cache in session state
        st.session_state.current_analysis = analysis
        st.session_state.waveform_png = waveform_png
        st.session_state.spectrogram_png = spectrogram_png
        st.session_state.pdf_bytes = pdf_bytes
        st.session_state.report_name = report_name
        st.session_state.report_path = report_path

# Display results if an analysis is active
if st.session_state.current_analysis is not None:
    analysis = st.session_state.current_analysis
    waveform_png = st.session_state.waveform_png
    spectrogram_png = st.session_state.spectrogram_png
    pdf_bytes = st.session_state.pdf_bytes
    report_name = st.session_state.report_name
    report_path = st.session_state.report_path

    res_header_cols = st.columns([3, 1])
    with res_header_cols[0]:
        st.success("🎉 Multimodal Evaluation Completed Successfully!")
    with res_header_cols[1]:
        if st.button("🔄 Clear / Reset Results", use_container_width=True, type="secondary"):
            st.session_state.current_analysis = None
            st.session_state.recorder_id += 1
            st.rerun()

    # ---------------- EXECUTIVE SCORECARD METRICS ----------------
    score_cols = st.columns(4)
    with score_cols[0]:
        st.metric(
            label="Overall Mastery Score",
            value=percent(analysis.score.overall_score),
            delta=analysis.score.understanding_level,
        )
    with score_cols[1]:
        blooms_val = analysis.blooms.level if analysis.blooms else "Understanding"
        st.metric(
            label="Cognitive Depth (Bloom's)",
            value=blooms_val,
            delta=f"Depth {int((analysis.blooms.depth_score if analysis.blooms else 0.5) * 100)}%",
        )
    with score_cols[2]:
        wpm_val = f"{analysis.prosody.words_per_minute} WPM" if analysis.prosody else "N/A"
        pacing_lbl = analysis.prosody.pacing_category if analysis.prosody else "Normal"
        st.metric(label="Speaking Pace", value=wpm_val, delta=pacing_lbl)
    with score_cols[3]:
        st.metric(
            label="Fluency & Delivery",
            value=percent(analysis.score.fluency_score),
            delta=analysis.score.communication_level,
        )

    st.write("")

    # ---------------- MODULAR TABS DASHBOARD ----------------
    tabs = st.tabs(
        [
            "🎯 Executive & Rubric Radar",
            "🧠 Cognitive Depth & Misconceptions",
            "🎙️ Speech Prosody & Acoustics",
            "🎓 Adaptive Viva-Voce (AI Examiner)",
            "📈 Progress & Cohort Analytics",
            "📄 Download PDF Report",
        ]
    )

    # --- TAB 1: EXECUTIVE & RUBRIC RADAR ---
    with tabs[0]:
        col_radar, col_details = st.columns([1.1, 1.4], gap="large")

        with col_radar:
            st.markdown("#### 🕸️ 5-Axis Pedagogical Rubric")
            if analysis.rubric:
                radar_bytes = create_radar_chart_png(analysis.rubric)
                if radar_bytes:
                    st.image(radar_bytes, caption="Pedagogical Evaluation Radar", use_container_width=True)
                radar_data = analysis.rubric.to_radar_dict()
                st.dataframe(
                    [{"Dimension": k, "Score": f"{v:.1f}%"} for k, v in radar_data.items()],
                    use_container_width=True,
                    hide_index=True,
                )

        with col_details:
            st.markdown("#### 📝 Diagnostic Summary & Feedback")
            st.info(analysis.summary)
            st.markdown("##### 📌 Key Recommendations:")
            for item in analysis.score.feedback:
                st.markdown(f"- {item}")

            if analysis.semantic.warnings or analysis.transcript.warnings or analysis.audio_features.warnings:
                st.warning(
                    "\n".join(
                        analysis.semantic.warnings
                        + analysis.transcript.warnings
                        + analysis.audio_features.warnings
                    )
                )

    # --- TAB 2: COGNITIVE DEPTH & MISCONCEPTIONS ---
    with tabs[1]:
        st.markdown("#### 🧠 Bloom's Taxonomy Cognitive Classification")
        if analysis.blooms:
            b_cols = st.columns(6)
            levels = ["Remembering", "Understanding", "Applying", "Analyzing", "Evaluating", "Creating"]
            for idx, lvl in enumerate(levels):
                with b_cols[idx]:
                    if lvl == analysis.blooms.level:
                        st.markdown(f"**🟢 {lvl}**\n*(Achieved)*")
                    else:
                        st.markdown(f"⚪ {lvl}")
            st.caption(f"**Level Details:** {analysis.blooms.description}")
            if analysis.blooms.indicators:
                st.write("**Identified Cognitive Evidence:** " + ", ".join(analysis.blooms.indicators))

        st.divider()

        st.markdown("#### ⚠️ Factual Misconceptions & Anti-Patterns")
        if analysis.misconceptions and analysis.misconceptions.has_misconceptions:
            for item in analysis.misconceptions.detected:
                st.error(
                    f"**Detected Misconception: {item.misconception_type} (Severity: {item.severity})**\n\n"
                    f"*Speaker stated:* \"{item.detected_phrase}\"\n\n"
                    f"💡 *Expert Clarification:* {item.explanation}"
                )
        else:
            st.success("✅ **Zero Conceptual Misconceptions Detected!** The explanation aligns with established definitions.")

        st.divider()

        st.markdown("#### 🗺️ Concept Ontology Coverage Map")
        if analysis.knowledge_graph:
            st.write(f"Ontological Coverage: **{analysis.knowledge_graph.coverage_ratio * 100:.1f}%**")
            st.markdown("**Demonstrated Terminology & Principles:**")
            if analysis.knowledge_graph.covered_terms:
                chips_cov = " ".join([f"<span class='badge-pill badge-covered'>✓ {t}</span>" for t in analysis.knowledge_graph.covered_terms])
                st.markdown(chips_cov, unsafe_allow_html=True)
            else:
                st.caption("None detected.")

            st.write("")
            st.markdown("**Omitted / Missing Terminology:**")
            if analysis.knowledge_graph.missing_terms:
                chips_mis = " ".join([f"<span class='badge-pill badge-missing'>✗ {t}</span>" for t in analysis.knowledge_graph.missing_terms])
                st.markdown(chips_mis, unsafe_allow_html=True)
            else:
                st.caption("All expected concepts were covered!")

    # --- TAB 3: SPEECH PROSODY & ACOUSTICS ---
    with tabs[2]:
        p_col1, p_col2, p_col3, p_col4 = st.columns(4)
        if analysis.prosody:
            p_col1.metric("Speaking Rate", f"{analysis.prosody.words_per_minute} WPM", analysis.prosody.pacing_category)
            p_col2.metric("Pitch Cadence", f"{analysis.prosody.pitch_variation_hz} Hz", analysis.prosody.pitch_expressiveness)
            p_col3.metric("Articulation Rate", f"{analysis.prosody.articulation_rate} w/s", "Active Speech")
            p_col4.metric("Hesitations", f"{analysis.prosody.hesitation_clusters} events", f"Filler Ratio: {percent(analysis.filler_stats.filler_ratio)}")

        st.write("")
        col_wave, col_spec = st.columns(2)
        with col_wave:
            if waveform_png:
                st.image(waveform_png, caption="Audio Waveform (Time vs Amplitude)", use_container_width=True)
        with col_spec:
            if spectrogram_png:
                st.image(spectrogram_png, caption="Frequency Spectrogram (Formants & Prosody)", use_container_width=True)

        if analysis.filler_stats.occurrences:
            st.markdown("##### 🗣️ Filler Word Distribution")
            st.bar_chart(analysis.filler_stats.occurrences)

        with st.expander("📜 Verbatim Transcript"):
            st.text_area("Full Transcript", value=analysis.transcript.text, height=180)
            st.caption(f"Transcription Engine: {analysis.transcript.engine}")

    # --- TAB 4: ADAPTIVE VIVA-VOCE (AI EXAMINER) ---
    with tabs[3]:
        st.markdown("#### 🎓 Adaptive Viva-Voce Oral Examiner")
        st.caption("Simulated oral examination: The AI examines your explanation and formulates probing follow-up questions targeting your specific omissions and cognitive level.")

        if analysis.viva and analysis.viva.questions:
            for idx, q in enumerate(analysis.viva.questions, 1):
                st.markdown(f"##### Question {idx}: `{q.question_type}`")
                st.markdown(f"**{q.question}**")
                st.caption(f"🎯 *Examiner Objective:* {q.context_gap}")
                with st.expander(f"💡 Click to reveal Model Answer Hint for Q{idx}"):
                    st.write(q.ideal_response_hint)
                viva_ans = st.text_input(f"Your Response to Question {idx}", key=f"viva_ans_{idx}")
                if viva_ans:
                    st.success("Response recorded! Demonstrates active engagement with follow-up probing.")
                st.divider()

    # --- TAB 5: PROGRESS & COHORT ANALYTICS ---
    with tabs[4]:
        st.markdown("#### 📈 Longitudinal Progress & Cohort History")
        rows = recent_results(limit=10)
        if rows:
            st.dataframe(
                [
                    {
                        "ID": r["result_id"],
                        "Topic": r["concept_title"],
                        "Overall Score": percent(r["overall_score"]),
                        "Bloom's Level": r["blooms_level"] or "Understanding",
                        "WPM": f"{r['wpm']:.1f}" if r["wpm"] else "N/A",
                        "Understanding": r["understanding_level"],
                        "Communication": r["communication_level"],
                        "Date": r["created_at"],
                    }
                    for r in rows
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No prior evaluation sessions found.")

    # --- TAB 6: PDF REPORT EXPORT ---
    with tabs[5]:
        st.markdown("#### 📄 Publication-Grade PDF Evaluation Report")
        st.write("Download an executive, multi-page diagnostic assessment report complete with radar charts, Bloom's badges, prosody metrics, and viva-voce questions.")
        st.download_button(
            "📥 Download Official PDF Report",
            data=pdf_bytes,
            file_name=report_name,
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
        st.caption(f"Saved locally to: `{report_path}`")

elif not analyze_clicked:
    st.info("💡 **Ready to evaluate:** Select a concept from the sidebar, record your voice or choose a file above, and click **Run Multimodal Evaluation**!")
