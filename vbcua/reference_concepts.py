from __future__ import annotations

from .models import ReferenceConcept

DEFAULT_CONCEPTS: tuple[ReferenceConcept, ...] = (
    # --- Artificial Intelligence & Machine Learning ---
    ReferenceConcept(
        title="Machine Learning",
        domain="AI & Machine Learning",
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
        subtopics=("Supervised Learning", "Unsupervised Learning", "Loss Function", "Overfitting & Regularization"),
    ),
    ReferenceConcept(
        title="Deep Neural Networks",
        domain="AI & Machine Learning",
        text=(
            "Deep neural networks are multilayered computational graphs inspired by "
            "biological neurons. They use interconnected layers including input, "
            "multiple hidden layers with non-linear activation functions, and output layers. "
            "Parameters are optimized through forward propagation, loss calculation, "
            "and backpropagation using gradient descent."
        ),
        key_terms=(
            "neural network",
            "layers",
            "activation function",
            "backpropagation",
            "gradient descent",
            "weights",
        ),
        subtopics=("Forward Propagation", "Backpropagation", "Activation Functions", "Vanishing Gradients"),
    ),
    ReferenceConcept(
        title="Artificial Intelligence",
        domain="AI & Machine Learning",
        text=(
            "Artificial intelligence is the field of building systems that can "
            "perform tasks normally associated with human intelligence, such "
            "as reasoning, learning, perception, language understanding, and "
            "decision making."
        ),
        key_terms=("reasoning", "learning", "perception", "language", "decision"),
        subtopics=("Knowledge Representation", "Search Algorithms", "Cognitive Systems", "Ethics in AI"),
    ),

    # --- Cloud & Distributed Systems ---
    ReferenceConcept(
        title="Cloud Computing",
        domain="Cloud & Systems",
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
        subtopics=("Service Models (IaaS/PaaS/SaaS)", "Elastic Scalability", "Virtualization", "Cloud Security"),
    ),
    ReferenceConcept(
        title="Operating System",
        domain="Cloud & Systems",
        text=(
            "An operating system manages computer hardware and software "
            "resources. It provides process scheduling, memory management, "
            "file systems, device management, and a user interface for running "
            "applications."
        ),
        key_terms=("process", "memory", "file system", "device", "applications"),
        subtopics=("CPU Scheduling", "Virtual Memory & Paging", "Inter-Process Communication", "Deadlocks"),
    ),
    ReferenceConcept(
        title="Microservices Architecture",
        domain="Cloud & Systems",
        text=(
            "Microservices architecture structures an application as a collection of "
            "small, loosely coupled, independently deployable services organized around "
            "business capabilities. Services communicate via lightweight protocols such as HTTP "
            "REST or message queues, enabling decentralized data management and high scalability."
        ),
        key_terms=("microservices", "loosely coupled", "deployable", "REST", "scalability", "decentralized"),
        subtopics=("API Gateway", "Service Discovery", "Event-Driven Messaging", "Fault Tolerance & Circuit Breakers"),
    ),

    # --- Databases & Data Architecture ---
    ReferenceConcept(
        title="Database Management System",
        domain="Databases & Data",
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
        subtopics=("Relational Algebra", "Query Optimization", "Indexing & B-Trees", "ACID Compliance"),
    ),
    ReferenceConcept(
        title="ACID Transactions",
        domain="Databases & Data",
        text=(
            "ACID transactions define the standard reliability guarantees in database management. "
            "Atomicity ensures all-or-nothing completion, Consistency maintains valid database states, "
            "Isolation prevents concurrent transaction interference, and Durability guarantees that committed "
            "changes survive system crashes."
        ),
        key_terms=("atomicity", "consistency", "isolation", "durability", "transactions", "commit"),
        subtopics=("Two-Phase Locking", "Write-Ahead Logging", "Isolation Levels", "Deadlock Resolution"),
    ),

    # --- Networks & Software Engineering ---
    ReferenceConcept(
        title="Computer Networks & TCP/IP",
        domain="Networking & Software",
        text=(
            "Computer networks connect distributed computing nodes to share data and resources. "
            "The TCP/IP stack structures network communication across Link, Internet, Transport, and Application layers. "
            "TCP ensures reliable, ordered packet delivery via three-way handshakes and flow control, while IP handles packet routing."
        ),
        key_terms=("networks", "TCP", "IP", "packets", "handshake", "routing", "transport"),
        subtopics=("Three-Way Handshake", "Flow & Congestion Control", "Subnetting & Addressing", "OSI vs TCP/IP"),
    ),
)


def concept_domains() -> list[str]:
    """Returns unique domain categories."""
    domains = []
    for c in DEFAULT_CONCEPTS:
        if c.domain not in domains:
            domains.append(c.domain)
    return domains


def concepts_by_domain(domain: str) -> list[ReferenceConcept]:
    """Returns concepts filtered by domain."""
    return [c for c in DEFAULT_CONCEPTS if c.domain == domain]


def concept_titles() -> list[str]:
    return [concept.title for concept in DEFAULT_CONCEPTS]


def get_reference_concept(title: str) -> ReferenceConcept:
    for concept in DEFAULT_CONCEPTS:
        if concept.title.lower() == title.lower():
            return concept
    raise KeyError(f"Unknown reference concept: {title}")
