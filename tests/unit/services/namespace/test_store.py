import sqlite3

import pytest

from talkingdb_nel.services.namespace import store


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    store.init_db(connection)
    yield connection
    connection.close()


def test_namespace_exists_false_when_missing(conn):
    assert store.namespace_exists(conn, "ns1") is False


def test_create_and_get_namespace(conn):
    created = store.create_namespace(conn, "ns1", description="first namespace")

    assert created["name"] == "ns1"
    assert created["description"] == "first namespace"
    assert "created_at" in created

    assert store.namespace_exists(conn, "ns1") is True
    assert store.get_namespace(conn, "ns1") == created


def test_get_namespace_missing_returns_none(conn):
    assert store.get_namespace(conn, "nope") is None


def test_update_namespace_description(conn):
    store.create_namespace(conn, "ns1", description="original")

    updated = store.update_namespace(conn, "ns1", "new description")

    assert updated["description"] == "new description"
    assert store.get_namespace(conn, "ns1")["description"] == "new description"


def test_update_namespace_missing_raises(conn):
    with pytest.raises(store.NamespaceNotFoundError):
        store.update_namespace(conn, "nope", "description")


def test_delete_namespace_removes_namespace_and_commits(conn):
    store.create_namespace(conn, "ns1")
    store.create_commit(conn, "ns1", "first", {})

    store.delete_namespace(conn, "ns1")

    assert store.namespace_exists(conn, "ns1") is False
    assert store.list_commits(conn, "ns1") == []


def test_delete_namespace_missing_raises(conn):
    with pytest.raises(store.NamespaceNotFoundError):
        store.delete_namespace(conn, "nope")


def test_delete_namespace_scoped_to_namespace(conn):
    store.create_namespace(conn, "ns1")
    store.create_namespace(conn, "ns2")
    store.create_commit(conn, "ns2", "ns2 commit", {})

    store.delete_namespace(conn, "ns1")

    assert store.namespace_exists(conn, "ns1") is False
    assert store.namespace_exists(conn, "ns2") is True
    assert len(store.list_commits(conn, "ns2")) == 1


def test_create_namespace_duplicate_raises(conn):
    store.create_namespace(conn, "ns1")

    with pytest.raises(store.NamespaceAlreadyExistsError):
        store.create_namespace(conn, "ns1")


def test_list_namespaces(conn):
    store.create_namespace(conn, "ns1")
    store.create_namespace(conn, "ns2")

    names = [n["name"] for n in store.list_namespaces(conn)]

    assert names == ["ns1", "ns2"]


def test_create_commit_first_has_no_parent(conn):
    store.create_namespace(conn, "ns1")

    commit = store.create_commit(conn, "ns1", "initial", {"entities": {}})

    assert commit["parent_commit_id"] is None
    assert commit["message"] == "initial"


def test_create_commit_chains_parent(conn):
    store.create_namespace(conn, "ns1")

    first = store.create_commit(conn, "ns1", "first", {})
    second = store.create_commit(conn, "ns1", "second", {})

    assert second["parent_commit_id"] == first["commit_id"]


def test_list_commits_most_recent_first(conn):
    store.create_namespace(conn, "ns1")

    first = store.create_commit(conn, "ns1", "first", {})
    second = store.create_commit(conn, "ns1", "second", {})

    commits = store.list_commits(conn, "ns1")

    assert [c["commit_id"] for c in commits] == [
        second["commit_id"],
        first["commit_id"],
    ]


def test_list_commits_scoped_to_namespace(conn):
    store.create_namespace(conn, "ns1")
    store.create_namespace(conn, "ns2")

    store.create_commit(conn, "ns1", "ns1 commit", {})
    store.create_commit(conn, "ns2", "ns2 commit", {})

    assert [c["message"] for c in store.list_commits(conn, "ns1")] == ["ns1 commit"]
    assert [c["message"] for c in store.list_commits(conn, "ns2")] == ["ns2 commit"]


def test_get_commit_includes_snapshot(conn):
    store.create_namespace(conn, "ns1")

    snapshot = {"entities": {"nodes": []}, "regex_rules": {}}
    created = store.create_commit(conn, "ns1", "initial", snapshot)

    result = store.get_commit(conn, "ns1", created["commit_id"])

    assert result["snapshot"] == snapshot
    assert result["message"] == "initial"


def test_get_commit_missing_returns_none(conn):
    store.create_namespace(conn, "ns1")

    assert store.get_commit(conn, "ns1", "nonexistent") is None
