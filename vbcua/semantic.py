from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache

from .config import SENTENCE_MODEL_NAME
from .models import ReferenceConcept, SemanticResult

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.-]*")


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]


def lexical_similarity(text_a: str, text_b: str) -> float:
    counts_a = Counter(tokenize(text_a))
    counts_b = Counter(tokenize(text_b))
    if not counts_a or not counts_b:
        return 0.0

    shared = set(counts_a) & set(counts_b)
    numerator = sum(counts_a[token] * counts_b[token] for token in shared)
    norm_a = math.sqrt(sum(value * value for value in counts_a.values()))
    norm_b = math.sqrt(sum(value * value for value in counts_b.values()))
    if not norm_a or not norm_b:
        return 0.0
    return max(0.0, min(1.0, numerator / (norm_a * norm_b)))


@lru_cache(maxsize=2)
def _load_sentence_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _embedding_similarity(text_a: str, text_b: str, model_name: str) -> float:
    import numpy as np

    model = _load_sentence_model(model_name)
    embeddings = model.encode([text_a, text_b], normalize_embeddings=True)
    score = float(np.dot(embeddings[0], embeddings[1]))
    return max(0.0, min(1.0, score))


def _missing_key_terms(transcript: str, key_terms: tuple[str, ...]) -> list[str]:
    transcript_norm = transcript.lower()
    missing = []
    for term in key_terms:
        normalized_term = term.lower()
        if normalized_term not in transcript_norm:
            term_tokens = set(tokenize(normalized_term))
            if term_tokens and not term_tokens.issubset(set(tokenize(transcript_norm))):
                missing.append(term)
    return missing


def evaluate_semantic_understanding(
    transcript: str,
    concept: ReferenceConcept,
    *,
    model_name: str = SENTENCE_MODEL_NAME,
) -> SemanticResult:
    warnings: list[str] = []
    if not transcript.strip():
        return SemanticResult(
            similarity_score=0.0,
            backend="none",
            missing_key_terms=list(concept.key_terms),
            warnings=["No transcript was available for semantic evaluation."],
        )

    try:
        score = _embedding_similarity(transcript, concept.text, model_name)
        backend = f"sentence-transformers:{model_name}"
    except ModuleNotFoundError:
        score = lexical_similarity(transcript, concept.text)
        backend = "lexical cosine fallback"
        warnings.append(
            "sentence-transformers is not installed; used lexical similarity fallback."
        )
    except Exception as exc:  # pragma: no cover - depends on local model runtime
        score = lexical_similarity(transcript, concept.text)
        backend = "lexical cosine fallback"
        warnings.append(f"Embedding model failed, used lexical fallback: {exc}")

    return SemanticResult(
        similarity_score=score,
        backend=backend,
        missing_key_terms=_missing_key_terms(transcript, concept.key_terms),
        warnings=warnings,
    )
