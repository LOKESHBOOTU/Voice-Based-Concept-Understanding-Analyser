from __future__ import annotations

import re
from .models import BloomsTaxonomyResult

BLOOMS_LEVELS = (
    ("Remembering", 0.35, [
        r"\b(?:defined as|means|is called|refers to|stands for|consists of|basic|term|concept)\b",
        r"\b(?:types of|components of|parts of|list of)\b",
    ], "Recalls foundational definitions, terminologies, and factual characteristics."),
    ("Understanding", 0.50, [
        r"\b(?:because|which means|in other words|explains|the reason|this implies|essentially|signifies)\b",
        r"\b(?:how it works|general idea|main goal|purpose of)\b",
    ], "Explains underlying concepts, interprets principles, and summarizes core mechanisms."),
    ("Applying", 0.65, [
        r"\b(?:for example|such as|for instance|applied in|real-world|practical|use case|implementation|scenario)\b",
        r"\b(?:used by|deploy|production|we can use|leverages)\b",
    ], "Connects theory to concrete real-world applications, engineering use cases, and implementations."),
    ("Analyzing", 0.80, [
        r"\b(?:compared to|versus|unlike|differs from|in contrast|breakdown|mechanism|tradeoff|difference between)\b",
        r"\b(?:classified into|relationship between|underlying architecture|decompose)\b",
    ], "Deconstructs mechanisms, compares paradigms, and distinguishes structural components."),
    ("Evaluating", 0.92, [
        r"\b(?:limitation|drawback|disadvantage|advantage|bottleneck|efficiency|overhead|evaluated by|metric)\b",
        r"\b(?:pros and cons|challenges|scalability issue|accuracy vs|trade-off)\b",
    ], "Critically assesses tradeoffs, architectural bottlenecks, performance constraints, and suitability."),
    ("Creating", 1.00, [
        r"\b(?:designing|architecting|synthesize|integrate|combine with|pipeline architecture|proposed solution)\b",
        r"\b(?:build an end-to-end|hybrid approach|novel system)\b",
    ], "Demonstrates holistic synthesis, architectural formulation, and systems-level problem solving."),
)


def evaluate_blooms_taxonomy(transcript: str, semantic_score: float = 0.5) -> BloomsTaxonomyResult:
    """Classifies cognitive depth according to Bloom's Revised Taxonomy."""
    text = transcript.lower().strip()
    if not text:
        return BloomsTaxonomyResult(
            level="Remembering",
            depth_score=0.2,
            indicators=["Minimal explanation provided."],
            description="The spoken answer was too brief to demonstrate conceptual depth.",
        )

    matched_levels: list[tuple[str, float, list[str], str]] = []

    for level_name, base_score, patterns, desc in BLOOMS_LEVELS:
        hits = []
        for pattern in patterns:
            found = re.findall(pattern, text)
            if found:
                hits.extend(found[:3])
        if hits:
            matched_levels.append((level_name, base_score, hits, desc))

    # If no explicit markers matched, fallback based on semantic score and explanation length
    words = len(re.findall(r"\w+", text))
    if not matched_levels:
        if words > 70 and semantic_score >= 0.7:
            level_name, base_score, _, desc = BLOOMS_LEVELS[1]  # Understanding
            return BloomsTaxonomyResult(
                level=level_name,
                depth_score=base_score,
                indicators=["Implicit conceptual coherence detected through vocabulary."],
                description=desc,
            )
        else:
            level_name, base_score, _, desc = BLOOMS_LEVELS[0]  # Remembering
            return BloomsTaxonomyResult(
                level=level_name,
                depth_score=base_score,
                indicators=["Basic vocabulary recall."],
                description=desc,
            )

    # Highest demonstrated cognitive level
    highest_level = matched_levels[-1]
    level_name, base_score, hits, desc = highest_level

    # Adjust depth score based on semantic understanding
    adjusted_score = round(max(0.2, min(1.0, (base_score * 0.75) + (semantic_score * 0.25))), 2)

    unique_indicators = list(dict.fromkeys(hits))[:4]
    indicator_summary = [f"Expressed '{ind}'" for ind in unique_indicators]

    return BloomsTaxonomyResult(
        level=level_name,
        depth_score=adjusted_score,
        indicators=indicator_summary,
        description=desc,
    )
