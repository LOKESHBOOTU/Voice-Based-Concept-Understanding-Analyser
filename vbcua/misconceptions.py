from __future__ import annotations

import re
from .models import MisconceptionItem, MisconceptionsResult, ReferenceConcept

# Catalog of known pedagogical misconceptions across computer science topics
COMMON_MISCONCEPTIONS = [
    {
        "concept_keyword": "machine learning",
        "patterns": [
            (
                r"\b(?:linear regression\s+(?:is|for)\s+classification|regression\s+(?:predicts|for)\s+labels)\b",
                "Confusing Regression with Classification",
                "Linear regression predicts continuous numerical values, whereas classification predicts discrete class labels.",
                "Medium",
            ),
            (
                r"\b(?:unsupervised\s+learning\s+(?:uses|requires|has)\s+labels|unsupervised\s+needs\s+supervision)\b",
                "Misunderstanding Unsupervised Learning",
                "Unsupervised learning deals with unlabeled data to discover underlying structures or clusters, not labeled training targets.",
                "High",
            ),
            (
                r"\b(?:overfitting\s+(?:means|happens when)\s+(?:the model is too simple|underlearns))\b",
                "Confusing Overfitting with Underfitting",
                "Overfitting occurs when a model learns noise and details in training data excessively (high variance), not when it is too simple.",
                "High",
            ),
            (
                r"\b(?:accuracy\s+is\s+always\s+(?:the best|sufficient)|high accuracy\s+means\s+no errors)\b",
                "Accuracy Paradox in Imbalanced Datasets",
                "Accuracy can be misleading on imbalanced datasets. Metrics like Precision, Recall, and F1-score are needed.",
                "Low",
            ),
        ],
    },
    {
        "concept_keyword": "cloud",
        "patterns": [
            (
                r"\b(?:cloud\s+is\s+just\s+free\s+storage|cloud\s+only\s+means\s+google drive)\b",
                "Trivializing Cloud Infrastructure",
                "Cloud computing encompasses full compute, storage, serverless, database, and networking architectures, not just file storage.",
                "Medium",
            ),
            (
                r"\b(?:saas\s+gives\s+(?:hardware|virtual machine|raw access))\b",
                "Confusing SaaS with IaaS",
                "Software-as-a-Service (SaaS) delivers ready-to-use software applications, whereas Infrastructure-as-a-Service (IaaS) provides virtual machines and raw compute.",
                "Medium",
            ),
        ],
    },
    {
        "concept_keyword": "operating system",
        "patterns": [
            (
                r"\b(?:ram\s+is\s+non-?volatile|ram\s+(?:keeps|saves)\s+data\s+(?:when|after)\s+(?:power\s+off|shutdown))\b",
                "Misunderstanding Volatile Memory",
                "RAM is volatile memory; its contents are lost when power is turned off. Persistent data must be saved to secondary storage.",
                "High",
            ),
            (
                r"\b(?:thread\s+has\s+its\s+own\s+independent\s+memory\s+space)\b",
                "Confusing Threads with Processes",
                "Threads within the same process share the same memory space (heap and code segment), while processes have isolated memory spaces.",
                "Medium",
            ),
        ],
    },
    {
        "concept_keyword": "database",
        "patterns": [
            (
                r"\b(?:nosql\s+means\s+no\s+sql\s+allowed|nosql\s+cannot\s+store\s+data)\b",
                "Literal Interpretation of NoSQL",
                "NoSQL stands for 'Not Only SQL', supporting flexible schemas (document, key-value, graph) rather than strictly disallowing SQL queries.",
                "Low",
            ),
            (
                r"\b(?:atomicity\s+means\s+fast\s+execution)\b",
                "Misunderstanding ACID Atomicity",
                "In ACID properties, Atomicity guarantees 'all-or-nothing' execution of transaction steps, not execution speed.",
                "Medium",
            ),
        ],
    },
    {
        "concept_keyword": "artificial intelligence",
        "patterns": [
            (
                r"\b(?:ai\s+and\s+machine\s+learning\s+are\s+(?:exactly the same|synonymous))\b",
                "Equating AI with Machine Learning",
                "Artificial Intelligence is the broader parent field; Machine Learning is a specific subset of AI focused on learning from data.",
                "Low",
            ),
        ],
    },
]


def detect_misconceptions(transcript: str, concept: ReferenceConcept) -> MisconceptionsResult:
    """Scans the transcript for common conceptual misunderstandings and anti-patterns."""
    text = transcript.lower()
    detected_items: list[MisconceptionItem] = []
    concept_title = concept.title.lower()

    for item in COMMON_MISCONCEPTIONS:
        keyword = item["concept_keyword"]
        # If the concept matches or the transcript talks heavily about this topic
        if keyword in concept_title or keyword in text:
            for pattern, name, explanation, severity in item["patterns"]:
                match = re.search(pattern, text)
                if match:
                    detected_items.append(
                        MisconceptionItem(
                            detected_phrase=match.group(0),
                            misconception_type=name,
                            explanation=explanation,
                            severity=severity,
                        )
                    )

    return MisconceptionsResult(
        detected=detected_items,
        has_misconceptions=len(detected_items) > 0,
    )
