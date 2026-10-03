from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from vbcua.config import REPORT_DIR, ensure_runtime_dirs
from vbcua.models import ReferenceConcept
from vbcua.pipeline import analyze_audio
from vbcua.reference_concepts import DEFAULT_CONCEPTS, concept_domains, concepts_by_domain, get_reference_concept
from vbcua.reporting import create_waveform_png, generate_pdf_report
from vbcua.storage import get_analytics_summary, init_db, recent_results, save_analysis, save_report_record

app = FastAPI(
    title="Voice-Based Concept Understanding Analyser (VBCUA) - Major Project API",
    description="Multimodal cognitive evaluation, speech prosody, Bloom's taxonomy, and adaptive viva-voce API.",
    version="2.0.0",
)


@app.on_event("startup")
def startup() -> None:
    ensure_runtime_dirs()
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "vbcua-major-project", "version": "2.0.0"}


@app.get("/domains")
def domains() -> list[str]:
    return concept_domains()


@app.get("/concepts")
def concepts(domain: str | None = None) -> list[dict[str, object]]:
    concept_list = concepts_by_domain(domain) if domain else list(DEFAULT_CONCEPTS)
    return [
        {
            "title": c.title,
            "domain": getattr(c, "domain", "General"),
            "text": c.text,
            "key_terms": list(c.key_terms),
            "subtopics": list(getattr(c, "subtopics", ())),
        }
        for c in concept_list
    ]


@app.get("/analytics")
def analytics() -> dict[str, object]:
    return get_analytics_summary()


@app.get("/results/recent")
def recent(limit: int = 10) -> list[dict[str, object]]:
    rows = recent_results(limit=limit)
    return [dict(row) for row in rows]


@app.post("/evaluate")
async def evaluate(
    audio: UploadFile = File(...),
    concept_title: str = Form("Machine Learning"),
    reference_text: str | None = Form(None),
    transcript_override: str | None = Form(None),
    generate_pdf: bool = Form(False),
) -> dict[str, object]:
    ensure_runtime_dirs()
    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await audio.read())
        temp_path = Path(temp_file.name)

    if reference_text:
        concept = ReferenceConcept(concept_title, reference_text)
    else:
        concept = get_reference_concept(concept_title)

    result = analyze_audio(temp_path, concept, transcript_override=transcript_override)
    result = save_analysis(result)

    response_data = result.to_dict()

    if generate_pdf:
        waveform_png = create_waveform_png(temp_path)
        pdf_bytes = generate_pdf_report(result, waveform_png)
        result_id = result.record_ids.get("result_id", 0)
        report_path = REPORT_DIR / f"vbcua_report_{result_id}.pdf"
        report_path.write_bytes(pdf_bytes)
        save_report_record(result_id, report_path, max(1, len(pdf_bytes) // 1024))
        response_data["pdf_report_path"] = str(report_path)

    return response_data


@app.get("/report/{result_id}")
def download_report(result_id: int):
    report_path = REPORT_DIR / f"vbcua_report_{result_id}.pdf"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="PDF report not found")
    return FileResponse(
        str(report_path),
        media_type="application/pdf",
        filename=f"vbcua_report_{result_id}.pdf",
    )
