from __future__ import annotations

from .models import ReferenceConcept


DEFAULT_CONCEPTS: tuple[ReferenceConcept, ...] = (
    ReferenceConcept(
        title="Machine Learning",
        text=(
            "Machine learning is a branch of artificial intelligence where "
            "computer systems learn patterns from data and improve their "
            "performance on tasks without being explicitly programmed for "
            "every rule. It includes supervised, unsupervised, and "
            "reinforcement learning approaches, and it is evaluated using "
            "measures such as accuracy, precision, recall, or error."
        ),
        key_terms=(
            "artificial intelligence",
            "data",
            "patterns",
            "supervised",
            "unsupervised",
            "reinforcement",
            "model",
        ),
    ),
    ReferenceConcept(
        title="Cloud Computing",
        text=(
            "Cloud computing delivers computing resources such as servers, "
            "storage, databases, networking, and software over the internet. "
            "It supports scalable, on-demand access and common service models "
            "such as infrastructure as a service, platform as a service, and "
            "software as a service."
        ),
        key_terms=(
            "internet",
            "servers",
            "storage",
            "scalable",
            "on-demand",
            "IaaS",
            "PaaS",
            "SaaS",
        ),
    ),
    ReferenceConcept(
        title="Artificial Intelligence",
        text=(
            "Artificial intelligence is the field of building systems that can "
            "perform tasks normally associated with human intelligence, such "
            "as reasoning, learning, perception, language understanding, and "
            "decision making."
        ),
        key_terms=("reasoning", "learning", "perception", "language", "decision"),
    ),
    ReferenceConcept(
        title="Database Management System",
        text=(
            "A database management system stores, organizes, retrieves, and "
            "protects structured data. It provides query processing, "
            "transactions, concurrency control, integrity constraints, and "
            "security for applications and users."
        ),
        key_terms=(
            "data",
            "query",
            "transactions",
            "concurrency",
            "integrity",
            "security",
        ),
    ),
    ReferenceConcept(
        title="Operating System",
        text=(
            "An operating system manages computer hardware and software "
            "resources. It provides process scheduling, memory management, "
            "file systems, device management, and a user interface for running "
            "applications."
        ),
        key_terms=("process", "memory", "file system", "device", "applications"),
    ),
)


def concept_titles() -> list[str]:
    return [concept.title for concept in DEFAULT_CONCEPTS]


def get_reference_concept(title: str) -> ReferenceConcept:
    for concept in DEFAULT_CONCEPTS:
        if concept.title == title:
            return concept
    raise KeyError(f"Unknown reference concept: {title}")
