from __future__ import annotations

import re
from .models import ConceptCoverageNode, KnowledgeGraphResult, ReferenceConcept


def extract_concept_graph(transcript: str, concept: ReferenceConcept) -> KnowledgeGraphResult:
    """Extracts concept coverage against the reference ontology and subtopics."""
    text_lower = transcript.lower()
    nodes: list[ConceptCoverageNode] = []
    covered_terms: list[str] = []
    missing_terms: list[str] = []

    # Combine key terms and any defined subtopics
    terms = list(concept.key_terms)
    subtopics = list(getattr(concept, "subtopics", ()))

    # If subtopics are present, use them for rich categorization
    categorized_terms: list[tuple[str, str]] = []
    for term in terms:
        categorized_terms.append((term, "Core Concept"))
    for sub in subtopics:
        if sub not in terms:
            categorized_terms.append((sub, "Sub-domain/Mechanism"))

    # If still small list, extract noun phrases / distinct keywords from concept text
    if len(categorized_terms) < 4 and concept.text:
        words = re.findall(r"\b[A-Za-z]{5,}\b", concept.text)
        stopwords = {"system", "delivers", "perform", "structure", "manages", "provides", "without"}
        unique_words = [w for w in set(words) if w.lower() not in stopwords]
        for w in unique_words[:6]:
            if not any(w.lower() == t[0].lower() for t in categorized_terms):
                categorized_terms.append((w, "Supporting Element"))

    for term, category in categorized_terms:
        # Check if term exists in transcript
        term_lower = term.lower()
        # Word boundary or phrase check
        pattern = rf"\b{re.escape(term_lower)}\b"
        match = re.search(pattern, text_lower)
        is_covered = bool(match)

        context_snippet = ""
        if is_covered and match:
            start = max(0, match.start() - 25)
            end = min(len(text_lower), match.end() + 25)
            context_snippet = f"...{text_lower[start:end].strip()}..."

        nodes.append(
            ConceptCoverageNode(
                name=term,
                category=category,
                covered=is_covered,
                context=context_snippet,
            )
        )

        if is_covered:
            covered_terms.append(term)
        else:
            missing_terms.append(term)

    total = len(nodes) or 1
    coverage_ratio = round(len(covered_terms) / total, 3)

    return KnowledgeGraphResult(
        nodes=nodes,
        coverage_ratio=coverage_ratio,
        covered_terms=covered_terms,
        missing_terms=missing_terms,
    )
