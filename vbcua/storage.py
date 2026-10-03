from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from typing import Iterator
from contextlib import contextmanager

from .config import DB_PATH
from .models import AnalysisResult, ReferenceConcept
from .reference_concepts import DEFAULT_CONCEPTS


SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100),
    email VARCHAR(150),
    role VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reference_concept (
    ref_concept_id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_title VARCHAR(255) UNIQUE NOT NULL,
    concept_text TEXT NOT NULL,
    key_terms TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audio_file (
    audio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    file_name VARCHAR(255),
    file_path VARCHAR(255),
    duration_sec FLOAT,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20),
    FOREIGN KEY(user_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS transcript (
    transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_id INTEGER NOT NULL,
    transcript_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(audio_id) REFERENCES audio_file(audio_id)
);

CREATE TABLE IF NOT EXISTS filler_word_stats (
    filler_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id INTEGER NOT NULL,
    filler_word_count INTEGER,
    total_words INTEGER,
    filler_ratio FLOAT,
    occurrences TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(transcript_id) REFERENCES transcript(transcript_id)
);

CREATE TABLE IF NOT EXISTS semantic_similarity (
    similarity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id INTEGER NOT NULL,
    ref_concept_id INTEGER NOT NULL,
    similarity_score FLOAT,
    backend VARCHAR(255),
    missing_key_terms TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(transcript_id) REFERENCES transcript(transcript_id),
    FOREIGN KEY(ref_concept_id) REFERENCES reference_concept(ref_concept_id)
);

CREATE TABLE IF NOT EXISTS audio_feature (
    feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_id INTEGER NOT NULL,
    pause_ratio FLOAT,
    rms_energy FLOAT,
    zero_crossing_rate FLOAT,
    duration_sec FLOAT,
    sample_rate INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(audio_id) REFERENCES audio_file(audio_id)
);

CREATE TABLE IF NOT EXISTS evaluation_result (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_id INTEGER NOT NULL,
    ref_concept_id INTEGER NOT NULL,
    overall_score FLOAT,
    semantic_score FLOAT,
    fluency_score FLOAT,
    sentiment_score FLOAT,
    sentiment_label VARCHAR(20),
    understanding_level VARCHAR(30),
    communication_level VARCHAR(30),
    blooms_level VARCHAR(30),
    wpm FLOAT,
    rubric_json TEXT,
    viva_json TEXT,
    summary TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(audio_id) REFERENCES audio_file(audio_id),
    FOREIGN KEY(ref_concept_id) REFERENCES reference_concept(ref_concept_id)
);

CREATE TABLE IF NOT EXISTS report (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,
    pdf_path VARCHAR(255),
    file_size_kb INTEGER,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(result_id) REFERENCES evaluation_result(result_id)
);

CREATE TABLE IF NOT EXISTS session (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    status VARCHAR(20),
    FOREIGN KEY(user_id) REFERENCES user(user_id)
);
"""


@contextmanager
def connect(db_path: str | Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(db_path: str | Path = DB_PATH) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)
        migrate_schema(connection)
        seed_reference_concepts(connection)


def migrate_schema(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(evaluation_result)").fetchall()
    }
    if "sentiment_score" not in columns:
        connection.execute(
            "ALTER TABLE evaluation_result ADD COLUMN sentiment_score FLOAT"
        )
    if "sentiment_label" not in columns:
        connection.execute(
            "ALTER TABLE evaluation_result ADD COLUMN sentiment_label VARCHAR(20)"
        )
    if "blooms_level" not in columns:
        connection.execute(
            "ALTER TABLE evaluation_result ADD COLUMN blooms_level VARCHAR(30)"
        )
    if "wpm" not in columns:
        connection.execute(
            "ALTER TABLE evaluation_result ADD COLUMN wpm FLOAT"
        )
    if "rubric_json" not in columns:
        connection.execute(
            "ALTER TABLE evaluation_result ADD COLUMN rubric_json TEXT"
        )
    if "viva_json" not in columns:
        connection.execute(
            "ALTER TABLE evaluation_result ADD COLUMN viva_json TEXT"
        )


def seed_reference_concepts(connection: sqlite3.Connection) -> None:
    for concept in DEFAULT_CONCEPTS:
        connection.execute(
            """
            INSERT OR IGNORE INTO reference_concept
                (concept_title, concept_text, key_terms)
            VALUES (?, ?, ?)
            """,
            (concept.title, concept.text, json.dumps(concept.key_terms)),
        )


def get_or_create_reference(
    connection: sqlite3.Connection, concept: ReferenceConcept
) -> int:
    existing = connection.execute(
        "SELECT ref_concept_id FROM reference_concept WHERE concept_title = ?",
        (concept.title,),
    ).fetchone()
    if existing:
        return int(existing["ref_concept_id"])

    cursor = connection.execute(
        """
        INSERT INTO reference_concept (concept_title, concept_text, key_terms)
        VALUES (?, ?, ?)
        """,
        (concept.title, concept.text, json.dumps(concept.key_terms)),
    )
    return int(cursor.lastrowid)


def save_analysis(
    result: AnalysisResult,
    *,
    db_path: str | Path = DB_PATH,
    user_name: str | None = None,
    user_email: str | None = None,
    role: str = "student",
) -> AnalysisResult:
    init_db(db_path)
    with connect(db_path) as connection:
        user_id = None
        if user_name or user_email:
            cursor = connection.execute(
                """
                INSERT INTO user (name, email, role)
                VALUES (?, ?, ?)
                """,
                (user_name, user_email, role),
            )
            user_id = int(cursor.lastrowid)

        ref_id = get_or_create_reference(connection, result.concept)

        audio_cursor = connection.execute(
            """
            INSERT INTO audio_file (user_id, file_name, file_path, duration_sec, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                result.audio_path.name,
                str(result.audio_path),
                result.audio_features.duration_sec,
                "processed",
            ),
        )
        audio_id = int(audio_cursor.lastrowid)

        transcript_cursor = connection.execute(
            """
            INSERT INTO transcript (audio_id, transcript_text)
            VALUES (?, ?)
            """,
            (audio_id, result.transcript.text),
        )
        transcript_id = int(transcript_cursor.lastrowid)

        connection.execute(
            """
            INSERT INTO filler_word_stats
                (transcript_id, filler_word_count, total_words, filler_ratio, occurrences)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                transcript_id,
                result.filler_stats.filler_word_count,
                result.filler_stats.total_words,
                result.filler_stats.filler_ratio,
                json.dumps(result.filler_stats.occurrences),
            ),
        )

        connection.execute(
            """
            INSERT INTO semantic_similarity
                (transcript_id, ref_concept_id, similarity_score, backend, missing_key_terms)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                transcript_id,
                ref_id,
                result.semantic.similarity_score,
                result.semantic.backend,
                json.dumps(result.semantic.missing_key_terms),
            ),
        )

        connection.execute(
            """
            INSERT INTO audio_feature
                (audio_id, pause_ratio, rms_energy, zero_crossing_rate, duration_sec, sample_rate)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                audio_id,
                result.audio_features.pause_ratio,
                result.audio_features.rms_energy,
                result.audio_features.zero_crossing_rate,
                result.audio_features.duration_sec,
                result.audio_features.sample_rate,
            ),
        )

        blooms_str = result.blooms.level if result.blooms else None
        wpm_val = result.prosody.words_per_minute if result.prosody else None
        rubric_str = json.dumps(asdict(result.rubric)) if result.rubric else None
        viva_str = json.dumps([asdict(q) for q in result.viva.questions]) if result.viva else None

        result_cursor = connection.execute(
            """
            INSERT INTO evaluation_result
                (
                    audio_id, ref_concept_id, overall_score, semantic_score,
                    fluency_score, sentiment_score, sentiment_label,
                    understanding_level, communication_level, blooms_level, wpm,
                    rubric_json, viva_json, summary, notes
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audio_id,
                ref_id,
                result.score.overall_score,
                result.score.semantic_score,
                result.score.fluency_score,
                result.sentiment.compound_score,
                result.sentiment.label,
                result.score.understanding_level,
                result.score.communication_level,
                blooms_str,
                wpm_val,
                rubric_str,
                viva_str,
                result.summary,
                "\n".join(result.score.feedback),
            ),
        )
        result_id = int(result_cursor.lastrowid)

        result.record_ids = {
            "user_id": user_id,
            "reference_concept_id": ref_id,
            "audio_id": audio_id,
            "transcript_id": transcript_id,
            "result_id": result_id,
        }
        return result


def save_report_record(
    result_id: int,
    pdf_path: str | Path,
    file_size_kb: int,
    *,
    db_path: str | Path = DB_PATH,
) -> int:
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO report (result_id, pdf_path, file_size_kb)
            VALUES (?, ?, ?)
            """,
            (result_id, str(pdf_path), file_size_kb),
        )
        return int(cursor.lastrowid)


def recent_results(limit: int = 15, db_path: str | Path = DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with connect(db_path) as connection:
        return list(
            connection.execute(
                """
                SELECT
                    er.result_id,
                    rc.concept_title,
                    er.overall_score,
                    er.understanding_level,
                    er.communication_level,
                    er.blooms_level,
                    er.wpm,
                    er.sentiment_label,
                    er.created_at
                FROM evaluation_result er
                JOIN reference_concept rc ON rc.ref_concept_id = er.ref_concept_id
                ORDER BY er.created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        )


def get_analytics_summary(db_path: str | Path = DB_PATH) -> dict[str, object]:
    """Retrieves aggregated performance analytics for learner dashboards."""
    init_db(db_path)
    with connect(db_path) as connection:
        total = connection.execute("SELECT COUNT(*) as cnt FROM evaluation_result").fetchone()["cnt"]
        if not total:
            return {"total_evaluations": 0, "avg_overall": 0.0, "avg_semantic": 0.0, "avg_fluency": 0.0}

        row = connection.execute(
            """
            SELECT
                COUNT(*) as count,
                AVG(overall_score) as avg_overall,
                AVG(semantic_score) as avg_semantic,
                AVG(fluency_score) as avg_fluency,
                AVG(wpm) as avg_wpm
            FROM evaluation_result
            """
        ).fetchone()

        return {
            "total_evaluations": row["count"],
            "avg_overall": round(float(row["avg_overall"] or 0.0) * 100, 1),
            "avg_semantic": round(float(row["avg_semantic"] or 0.0) * 100, 1),
            "avg_fluency": round(float(row["avg_fluency"] or 0.0) * 100, 1),
            "avg_wpm": round(float(row["avg_wpm"] or 0.0), 1),
        }
