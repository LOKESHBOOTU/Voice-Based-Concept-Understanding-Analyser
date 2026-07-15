from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, UploadFile

from vbcua.config import ensure_runtime_dirs
from vbcua.models import ReferenceConcept
from vbcua.pipeline import analyze_audio
from vbcua.reference_concepts import DEFAULT_CONCEPTS, get_reference_concept
from vbcua.storage import init_db, save_analysis

app = FastAPI(title="Voice-Based Concept Understanding Analyser API")


@app.on_event("startup")
def startup() -> None:
    ensure_runtime_dirs()
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "vbcua"}


@app.get("/concepts")
def concepts() -> list[dict[str, object]]:
    return [
        {
            "title": concept.title,
            "text": concept.text,
            "key_terms": list(concept.key_terms),
        }
        for concept in DEFAULT_CONCEPTS
    ]


@app.post("/evaluate")
async def evaluate(
    audio: UploadFile = File(...),
    concept_title: str = Form("Machine Learning"),
    reference_text: str | None = Form(None),
    transcript_override: str | None = Form(None),
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
    return result.to_dict()
