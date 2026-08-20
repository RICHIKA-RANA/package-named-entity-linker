import sqlite3

import pytest

from talkingdb_nel.services.testsuite import store


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    store.init_db(connection)
    yield connection
    connection.close()


def test_create_and_get_test_case(conn):
    created = store.create_test_case(
        conn,
        "ns1",
        message_text="mayank works at acme",
        word_correction=True,
        expected=[{"surface_text": "mayank", "entity_id": "mayank"}],
    )

    assert created["message_text"] == "mayank works at acme"
    assert created["word_correction"] is True
    assert created["expected"] == [{"surface_text": "mayank", "entity_id": "mayank"}]
    assert created["review_status"] == "pending"

    assert store.get_test_case(conn, "ns1", created["id"]) == created


def test_create_test_case_defaults(conn):
    created = store.create_test_case(conn, "ns1", message_text="hello")

    assert created["word_correction"] is False
    assert created["expected"] is None


def test_get_test_case_missing_returns_none(conn):
    assert store.get_test_case(conn, "ns1", "nope") is None


def test_list_test_cases_scoped_to_namespace(conn):
    store.create_test_case(conn, "ns1", message_text="a")
    store.create_test_case(conn, "ns2", message_text="b")

    assert [c["message_text"] for c in store.list_test_cases(conn, "ns1")] == ["a"]
    assert [c["message_text"] for c in store.list_test_cases(conn, "ns2")] == ["b"]


def test_update_test_case_partial_fields_leave_others_unchanged(conn):
    created = store.create_test_case(
        conn, "ns1", message_text="original", word_correction=True
    )

    updated = store.update_test_case(conn, "ns1", created["id"], message_text="edited")

    assert updated["message_text"] == "edited"
    assert updated["word_correction"] is True
    assert updated["expected"] is None


def test_update_test_case_can_set_expected(conn):
    created = store.create_test_case(conn, "ns1", message_text="msg")

    updated = store.update_test_case(
        conn,
        "ns1",
        created["id"],
        expected=[{"surface_text": "a", "entity_id": "A"}],
        review_status="accepted",
    )

    assert updated["expected"] == [{"surface_text": "a", "entity_id": "A"}]
    assert updated["review_status"] == "accepted"


def test_update_test_case_can_clear_expected(conn):
    created = store.create_test_case(
        conn,
        "ns1",
        message_text="msg",
        expected=[{"surface_text": "a", "entity_id": "A"}],
    )

    updated = store.update_test_case(conn, "ns1", created["id"], expected=None)

    assert updated["expected"] is None


def test_update_test_case_missing_raises(conn):
    with pytest.raises(store.TestCaseNotFoundError):
        store.update_test_case(conn, "ns1", "nope", message_text="x")


def test_delete_test_case_removes_it_and_its_results(conn):
    created = store.create_test_case(conn, "ns1", message_text="msg")
    run = store.create_run(conn, "ns1")
    store.create_run_result(conn, run["id"], created["id"], [], True, "new")

    store.delete_test_case(conn, "ns1", created["id"])

    assert store.get_test_case(conn, "ns1", created["id"]) is None
    assert store.list_run_results(conn, run["id"]) == []


def test_delete_test_case_missing_raises(conn):
    with pytest.raises(store.TestCaseNotFoundError):
        store.delete_test_case(conn, "ns1", "nope")


def test_create_run_and_get(conn):
    created = store.create_run(conn, "ns1", triggering_commit_id="c1")

    assert created["namespace"] == "ns1"
    assert created["triggering_commit_id"] == "c1"
    assert store.get_run(conn, "ns1", created["id"]) == created


def test_list_runs_most_recent_first(conn):
    first = store.create_run(conn, "ns1")
    second = store.create_run(conn, "ns1")

    ids = [r["id"] for r in store.list_runs(conn, "ns1")]

    assert ids == [second["id"], first["id"]]


def test_create_run_result_and_list(conn):
    case = store.create_test_case(conn, "ns1", message_text="msg")
    run = store.create_run(conn, "ns1")

    result = store.create_run_result(
        conn,
        run["id"],
        case["id"],
        [{"surface_text": "a", "entity_id": "A"}],
        True,
        "pass",
    )

    assert result["passed"] is True
    assert store.list_run_results(conn, run["id"]) == [result]


def test_create_run_result_needs_review_has_null_passed(conn):
    case = store.create_test_case(conn, "ns1", message_text="msg")
    run = store.create_run(conn, "ns1")

    result = store.create_run_result(
        conn, run["id"], case["id"], [], None, "needs_review"
    )

    assert result["passed"] is None
    assert store.list_run_results(conn, run["id"])[0]["passed"] is None


def test_get_latest_result_for_case_returns_most_recent(conn):
    case = store.create_test_case(conn, "ns1", message_text="msg")
    run1 = store.create_run(conn, "ns1")
    run2 = store.create_run(conn, "ns1")

    store.create_run_result(conn, run1["id"], case["id"], [], True, "new")
    latest = store.create_run_result(
        conn, run2["id"], case["id"], [], False, "regression"
    )

    assert store.get_latest_result_for_case(conn, case["id"]) == latest


def test_get_latest_result_for_case_none_when_never_run(conn):
    case = store.create_test_case(conn, "ns1", message_text="msg")

    assert store.get_latest_result_for_case(conn, case["id"]) is None
