from __future__ import annotations

from .models import (
    BloomsTaxonomyResult,
    KnowledgeGraphResult,
    MisconceptionsResult,
    ReferenceConcept,
    VivaQuestion,
    VivaResult,
)


def generate_viva_questions(
    concept: ReferenceConcept,
    knowledge_graph: KnowledgeGraphResult,
    blooms: BloomsTaxonomyResult | None,
    misconceptions: MisconceptionsResult | None,
) -> VivaResult:
    """Generates targeted Viva-Voce oral exam questions tailored to the student's gaps."""
    questions: list[VivaQuestion] = []

    # 1. Misconception Follow-up (High priority if any detected)
    if misconceptions and misconceptions.has_misconceptions:
        misc = misconceptions.detected[0]
        questions.append(
            VivaQuestion(
                question=(
                    f"During your explanation you mentioned '{misc.detected_phrase}'. "
                    f"Could you clarify the technical distinction regarding {misc.misconception_type}?"
                ),
                question_type="Misconception Clarification",
                context_gap=f"Address {misc.misconception_type}",
                ideal_response_hint=misc.explanation,
            )
        )

    # 2. Foundational Gap Question (based on missing key terms)
    if knowledge_graph.missing_terms:
        missing_term = knowledge_graph.missing_terms[0]
        questions.append(
            VivaQuestion(
                question=(
                    f"You covered the overview of {concept.title} nicely, but did not discuss '{missing_term}'. "
                    f"How does '{missing_term}' play an integral role in this domain?"
                ),
                question_type="Foundational Gap",
                context_gap=f"Missing explanation for '{missing_term}'",
                ideal_response_hint=f"Define and explain how {missing_term} connects with {concept.title}.",
            )
        )
    else:
        questions.append(
            VivaQuestion(
                question=(
                    f"You covered the core terms of {concept.title} thoroughly. "
                    "Can you walk me through the lifecycle or step-by-step workflow in a production environment?"
                ),
                question_type="Lifecycle Exploration",
                context_gap="Demonstrate end-to-end production workflow",
                ideal_response_hint=f"Describe the stages involved when deploying {concept.title} into production.",
            )
        )

    # 3. Cognitive Deep-Dive or Analytical Tradeoff Question
    current_level = blooms.level if blooms else "Understanding"
    if current_level in ("Remembering", "Understanding"):
        # Push to Analyzing / Applying
        questions.append(
            VivaQuestion(
                question=(
                    f"If you were asked to implement {concept.title} for a high-concurrency, latency-critical application, "
                    "what primary architectural bottleneck or tradeoff would you need to anticipate?"
                ),
                question_type="Analytical Tradeoff",
                context_gap="Elevate cognitive depth from definition to critical evaluation",
                ideal_response_hint="Discuss performance overheads, scalability limits, and mitigating strategies.",
            )
        )
    else:
        # Push to Evaluating / Creating
        questions.append(
            VivaQuestion(
                question=(
                    f"Compare {concept.title} with a competing paradigm or legacy architecture. "
                    "In what specific edge cases would you deliberately choose NOT to adopt it?"
                ),
                question_type="Edge Case Evaluation",
                context_gap="Demonstrate mastery of failure modes and architectural alternatives",
                ideal_response_hint="Provide an objective comparison showing when alternative designs are superior.",
            )
        )

    # Ensure at least 3 distinct questions are always formulated
    if len(questions) < 3 and len(knowledge_graph.missing_terms) > 1:
        term2 = knowledge_graph.missing_terms[1]
        questions.append(
            VivaQuestion(
                question=f"Could you provide a concrete industry use-case demonstrating how '{term2}' is applied?",
                question_type="Application Use-Case",
                context_gap=f"Practical illustration of {term2}",
                ideal_response_hint=f"Describe an industry example leveraging {term2}.",
            )
        )

    fallback_prompts = [
        (
            f"How would you optimize or scale {concept.title} under heavy production workload or resource constraints?",
            "Scalability & Optimization",
            "Demonstrate system tuning and optimization",
            f"Detail strategies such as caching, parallelism, or algorithmic pruning for {concept.title}.",
        ),
        (
            f"Could you describe a real-world scenario where an unexpected edge case occurs in {concept.title} and how you would diagnose it?",
            "Troubleshooting & Diagnostics",
            "Practical troubleshooting and error recovery",
            f"Explain common runtime errors, logging, and recovery mechanisms in {concept.title}.",
        ),
    ]

    fb_idx = 0
    while len(questions) < 3 and fb_idx < len(fallback_prompts):
        q_text, q_type, gap, hint = fallback_prompts[fb_idx]
        questions.append(
            VivaQuestion(
                question=q_text,
                question_type=q_type,
                context_gap=gap,
                ideal_response_hint=hint,
            )
        )
        fb_idx += 1

    return VivaResult(questions=questions[:3])
