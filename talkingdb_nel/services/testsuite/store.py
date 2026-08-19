import json
import sqlite3
import uuid
from datetime import datetime, timezone


class TestCaseNotFoundError(Exception):
    """Raised when a referenced test_case_id does not exist."""


class TestRunNotFoundError(Exception):
    """Raised when a referenced run_id does not exist."""


_UNSET = object()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS test_cases (
            id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            message_text TEXT NOT NULL,
            word_correction INTEGER NOT NULL DEFAULT 0,
            expected TEXT,
            review_status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_test_cases_namespace
        ON test_cases(namespace, created_at);

        CREATE TABLE IF NOT EXISTS test_runs (
            id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            created_at TEXT NOT NULL,
            triggering_commit_id TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_test_runs_namespace
        ON test_runs(namespace, created_at);

        CREATE TABLE IF NOT EXISTS test_run_results (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            test_case_id TEXT NOT NULL,
            actual TEXT NOT NULL,
            passed INTEGER,
            status_label TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_test_run_results_run
        ON test_run_results(run_id);

        CREATE INDEX IF NOT EXISTS idx_test_run_results_case
        ON test_run_results(test_case_id, created_at);
        """
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_test_case(row: sqlite3.Row) -> dict:
    result = dict(row)
    result["word_correction"] = bool(result["word_correction"])
    result["expected"] = json.loads(result["expected"]) if result["expected"] else None
    return result


def create_test_case(
    conn: sqlite3.Connection,
    namespace: str,
    message_text: str,
    word_correction: bool = False,
    expected: list[dict] | None = None,
) -> dict:
    test_case_id = str(uuid.uuid4())

    conn.execute(
        """
        INSERT INTO test_cases (
            id, namespace, message_text, word_correction, expected,
            review_status, created_at
        )
        VALUES (?, ?, ?, ?, ?, 'pending', ?)
        """,
        (
            test_case_id,
            namespace,
            message_text,
            int(word_correction),
            json.dumps(expected) if expected is not None else None,
            _now(),
        ),
    )

    return get_test_case(conn, namespace, test_case_id)


def get_test_case(
    conn: sqlite3.Connection, namespace: str, test_case_id: str
) -> dict | None:
    row = conn.execute(
        "SELECT * FROM test_cases WHERE namespace = ? AND id = ?",
        (namespace, test_case_id),
    ).fetchone()

    return _row_to_test_case(row) if row else None


def list_test_cases(conn: sqlite3.Connection, namespace: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM test_cases WHERE namespace = ? ORDER BY created_at",
        (namespace,),
    ).fetchall()

    return [_row_to_test_case(row) for row in rows]


def update_test_case(
    conn: sqlite3.Connection,
    namespace: str,
    test_case_id: str,
    message_text: str | None = None,
    word_correction: bool | None = None,
    expected=_UNSET,
    review_status: str | None = None,
) -> dict:
    existing = get_test_case(conn, namespace, test_case_id)

    if existing is None:
        raise TestCaseNotFoundError(test_case_id)

    new_message_text = (
        existing["message_text"] if message_text is None else message_text
    )
    new_word_correction = (
        existing["word_correction"] if word_correction is None else word_correction
    )
    new_expected = existing["expected"] if expected is _UNSET else expected
    new_review_status = (
        existing["review_status"] if review_status is None else review_status
    )

    conn.execute(
        """
        UPDATE test_cases
        SET message_text = ?, word_correction = ?, expected = ?, review_status = ?
        WHERE namespace = ? AND id = ?
        """,
        (
            new_message_text,
            int(new_word_correction),
            json.dumps(new_expected) if new_expected is not None else None,
            new_review_status,
            namespace,
            test_case_id,
        ),
    )

    return get_test_case(conn, namespace, test_case_id)


def delete_test_case(
    conn: sqlite3.Connection, namespace: str, test_case_id: str
) -> None:
    if get_test_case(conn, namespace, test_case_id) is None:
        raise TestCaseNotFoundError(test_case_id)

    conn.execute(
        "DELETE FROM test_cases WHERE namespace = ? AND id = ?",
        (namespace, test_case_id),
    )
    conn.execute(
        "DELETE FROM test_run_results WHERE test_case_id = ?",
        (test_case_id,),
    )


def create_run(
    conn: sqlite3.Connection,
    namespace: str,
    triggering_commit_id: str | None = None,
) -> dict:
    run_id = str(uuid.uuid4())

    conn.execute(
        """
        INSERT INTO test_runs (id, namespace, created_at, triggering_commit_id)
        VALUES (?, ?, ?, ?)
        """,
        (run_id, namespace, _now(), triggering_commit_id),
    )

    return get_run(conn, namespace, run_id)


def get_run(conn: sqlite3.Connection, namespace: str, run_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT id, namespace, created_at, triggering_commit_id
        FROM test_runs
        WHERE namespace = ? AND id = ?
        """,
        (namespace, run_id),
    ).fetchone()

    return dict(row) if row else None


def list_runs(conn: sqlite3.Connection, namespace: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, namespace, created_at, triggering_commit_id
        FROM test_runs
        WHERE namespace = ?
        ORDER BY created_at DESC
        """,
        (namespace,),
    ).fetchall()

    return [dict(row) for row in rows]


def _row_to_run_result(row: sqlite3.Row) -> dict:
    result = dict(row)
    result["actual"] = json.loads(result["actual"])
    result["passed"] = None if result["passed"] is None else bool(result["passed"])
    return result


def get_run_result(conn: sqlite3.Connection, result_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM test_run_results WHERE id = ?",
        (result_id,),
    ).fetchone()

    return _row_to_run_result(row) if row else None


def create_run_result(
    conn: sqlite3.Connection,
    run_id: str,
    test_case_id: str,
    actual: list[dict],
    passed: bool | None,
    status_label: str,
) -> dict:
    result_id = str(uuid.uuid4())

    conn.execute(
        """
        INSERT INTO test_run_results (
            id, run_id, test_case_id, actual, passed, status_label, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result_id,
            run_id,
            test_case_id,
            json.dumps(actual),
            None if passed is None else int(passed),
            status_label,
            _now(),
        ),
    )

    return get_run_result(conn, result_id)


def get_latest_result_for_case(
    conn: sqlite3.Connection, test_case_id: str
) -> dict | None:
    row = conn.execute(
        """
        SELECT *
        FROM test_run_results
        WHERE test_case_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (test_case_id,),
    ).fetchone()

    return _row_to_run_result(row) if row else None


def list_run_results(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM test_run_results WHERE run_id = ? ORDER BY created_at",
        (run_id,),
    ).fetchall()

    return [_row_to_run_result(row) for row in rows]
