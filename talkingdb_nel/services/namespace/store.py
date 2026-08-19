import json
import sqlite3
import uuid
from datetime import datetime, timezone


class NamespaceAlreadyExistsError(Exception):
    """Raised when creating a namespace name that already exists."""


class NamespaceNotFoundError(Exception):
    """Raised when a referenced namespace does not exist."""


class CommitNotFoundError(Exception):
    """Raised when a referenced commit_id does not exist for a namespace."""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS namespaces (
            name TEXT PRIMARY KEY,
            description TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS commits (
            namespace TEXT NOT NULL,
            commit_id TEXT NOT NULL,
            parent_commit_id TEXT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            snapshot_json TEXT NOT NULL,
            PRIMARY KEY (namespace, commit_id)
        );

        CREATE INDEX IF NOT EXISTS idx_commits_namespace
        ON commits(namespace, created_at);
        """
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def namespace_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM namespaces WHERE name = ?",
        (name,),
    ).fetchone()

    return row is not None


def create_namespace(
    conn: sqlite3.Connection,
    name: str,
    description: str | None = None,
) -> dict:
    if namespace_exists(conn, name):
        raise NamespaceAlreadyExistsError(name)

    conn.execute(
        """
        INSERT INTO namespaces (name, description, created_at)
        VALUES (?, ?, ?)
        """,
        (name, description, _now()),
    )

    return get_namespace(conn, name)


def get_namespace(conn: sqlite3.Connection, name: str) -> dict | None:
    row = conn.execute(
        "SELECT name, description, created_at FROM namespaces WHERE name = ?",
        (name,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def update_namespace(
    conn: sqlite3.Connection,
    name: str,
    description: str | None,
) -> dict:
    if not namespace_exists(conn, name):
        raise NamespaceNotFoundError(name)

    conn.execute(
        "UPDATE namespaces SET description = ? WHERE name = ?",
        (description, name),
    )

    return get_namespace(conn, name)


def delete_namespace(conn: sqlite3.Connection, name: str) -> None:
    if not namespace_exists(conn, name):
        raise NamespaceNotFoundError(name)

    conn.execute("DELETE FROM commits WHERE namespace = ?", (name,))
    conn.execute("DELETE FROM namespaces WHERE name = ?", (name,))


def list_namespaces(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT name, description, created_at FROM namespaces ORDER BY created_at"
    ).fetchall()

    return [dict(row) for row in rows]


def _latest_commit_id(conn: sqlite3.Connection, namespace: str) -> str | None:
    row = conn.execute(
        """
        SELECT commit_id
        FROM commits
        WHERE namespace = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (namespace,),
    ).fetchone()

    return row["commit_id"] if row else None


def create_commit(
    conn: sqlite3.Connection,
    namespace: str,
    message: str,
    snapshot: dict,
) -> dict:
    commit_id = str(uuid.uuid4())
    parent_commit_id = _latest_commit_id(conn, namespace)
    created_at = _now()

    conn.execute(
        """
        INSERT INTO commits (
            namespace, commit_id, parent_commit_id, message, created_at, snapshot_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            namespace,
            commit_id,
            parent_commit_id,
            message,
            created_at,
            json.dumps(snapshot),
        ),
    )

    return {
        "commit_id": commit_id,
        "parent_commit_id": parent_commit_id,
        "message": message,
        "created_at": created_at,
    }


def list_commits(conn: sqlite3.Connection, namespace: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT commit_id, parent_commit_id, message, created_at
        FROM commits
        WHERE namespace = ?
        ORDER BY created_at DESC
        """,
        (namespace,),
    ).fetchall()

    return [dict(row) for row in rows]


def get_commit(conn: sqlite3.Connection, namespace: str, commit_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT commit_id, parent_commit_id, message, created_at, snapshot_json
        FROM commits
        WHERE namespace = ? AND commit_id = ?
        """,
        (namespace, commit_id),
    ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["snapshot"] = json.loads(result.pop("snapshot_json"))

    return result
