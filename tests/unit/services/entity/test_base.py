import sqlite3

from talkingdb_nel.services.entity import base


def test_connections_created():
    assert base.dictionary_conn is not None
    assert base.entity_conn is not None
    assert base.regex_conn is not None


def test_dictionary_row_factory():
    assert base.dictionary_conn.row_factory is sqlite3.Row


def test_namespace_tables_initialized():
    # init_namespace_db(entity_conn) runs at import time - verify the
    # tables it creates actually exist on the shared connection.
    tables = {
        row["name"]
        for row in base.entity_conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    assert "namespaces" in tables
    assert "commits" in tables
