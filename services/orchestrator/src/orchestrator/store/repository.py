import os
from contextlib import contextmanager
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

DEMO_USER_EMAIL = "demo@learn-divine-speed.local"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/lgs"
    )


@contextmanager
def get_conn():
    conn = psycopg.connect(_database_url(), row_factory=dict_row, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


def get_or_create_demo_user() -> UUID:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = %s", (DEMO_USER_EMAIL,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute(
            "INSERT INTO users (email) VALUES (%s) RETURNING id", (DEMO_USER_EMAIL,)
        )
        return cur.fetchone()["id"]


def create_session(user_id: UUID, framework: str, goal: str, goal_context: dict | None) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sessions (user_id, framework, goal, goal_context, phase)
            VALUES (%s, %s, %s, %s, 'intake')
            RETURNING *
            """,
            (user_id, framework, goal, Jsonb(goal_context) if goal_context else None),
        )
        return cur.fetchone()


def get_session(session_id: UUID) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
        return cur.fetchone()


def update_session(session_id: UUID, **fields) -> dict:
    set_clause = ", ".join(f"{key} = %s" for key in fields)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE sessions SET {set_clause}, updated_at = now() WHERE id = %s RETURNING *",
            (*fields.values(), session_id),
        )
        return cur.fetchone()


def insert_diagnostic_question(session_id: UUID, question_text: str) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO diagnostic_responses (session_id, question_text) VALUES (%s, %s) RETURNING *",
            (session_id, question_text),
        )
        return cur.fetchone()


def get_pending_diagnostic_question(session_id: UUID) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM diagnostic_responses
            WHERE session_id = %s AND answer IS NULL
            ORDER BY asked_at DESC LIMIT 1
            """,
            (session_id,),
        )
        return cur.fetchone()


def answer_diagnostic_question(response_id: UUID, answer: str, correct: bool) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE diagnostic_responses SET answer = %s, correct = %s WHERE id = %s",
            (answer, correct, response_id),
        )


def count_answered_diagnostics(session_id: UUID) -> tuple[int, int]:
    """Returns (answered_count, correct_count)."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) AS total, count(*) FILTER (WHERE correct) AS correct "
            "FROM diagnostic_responses WHERE session_id = %s AND answer IS NOT NULL",
            (session_id,),
        )
        row = cur.fetchone()
        return row["total"], row["correct"]


def create_syllabus(session_id: UUID, framework: str) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO syllabi (session_id, framework) VALUES (%s, %s) RETURNING *",
            (session_id, framework),
        )
        return cur.fetchone()


def add_syllabus_concept(
    syllabus_id: UUID, ordinal: int, name: str, description: str, difficulty: str,
    prereq_concept_ids: list[UUID],
) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO syllabus_concepts
                (syllabus_id, ordinal, name, description, difficulty, prereq_concept_ids)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (syllabus_id, ordinal, name, description, difficulty, prereq_concept_ids),
        )
        return cur.fetchone()


def get_syllabus_with_concepts(syllabus_id: UUID) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM syllabi WHERE id = %s", (syllabus_id,))
        syllabus = cur.fetchone()
        if syllabus is None:
            return None
        cur.execute(
            "SELECT * FROM syllabus_concepts WHERE syllabus_id = %s ORDER BY ordinal",
            (syllabus_id,),
        )
        syllabus["concepts"] = cur.fetchall()
        return syllabus


def get_concept(concept_id: UUID) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM syllabus_concepts WHERE id = %s", (concept_id,))
        return cur.fetchone()


def update_concept_status(concept_id: UUID, status: str) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE syllabus_concepts SET status = %s WHERE id = %s", (status, concept_id))


def next_pending_concept(syllabus_id: UUID) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM syllabus_concepts WHERE syllabus_id = %s AND status = 'pending' "
            "ORDER BY ordinal LIMIT 1",
            (syllabus_id,),
        )
        return cur.fetchone()


def get_or_create_mastery_entry(session_id: UUID, concept_id: UUID) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM mastery_entries WHERE session_id = %s AND concept_id = %s",
            (session_id, concept_id),
        )
        row = cur.fetchone()
        if row:
            return row
        cur.execute(
            "INSERT INTO mastery_entries (session_id, concept_id) VALUES (%s, %s) RETURNING *",
            (session_id, concept_id),
        )
        return cur.fetchone()


def update_mastery_entry(entry_id: UUID, **fields) -> dict:
    set_clause = ", ".join(f"{key} = %s" for key in fields)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE mastery_entries SET {set_clause}, updated_at = now() WHERE id = %s RETURNING *",
            (*fields.values(), entry_id),
        )
        return cur.fetchone()


def list_mastery_entries(session_id: UUID) -> list[dict]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM mastery_entries WHERE session_id = %s", (session_id,))
        return cur.fetchall()


def insert_submission(
    session_id: UUID, concept_id: UUID, code: str, result_status: str,
    stdout: str, stderr: str, hint_given: str | None,
) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO submissions (session_id, concept_id, code, result_status, stdout, stderr, hint_given)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (session_id, concept_id, code, result_status, stdout, stderr, hint_given),
        )
        return cur.fetchone()
