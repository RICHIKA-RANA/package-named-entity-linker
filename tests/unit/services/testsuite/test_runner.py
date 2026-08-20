import sqlite3
from types import SimpleNamespace

import pytest

from talkingdb_nel.services.testsuite import runner, store


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    store.init_db(connection)
    yield connection
    connection.close()


def make_bundle(namespace: str) -> SimpleNamespace:
    return SimpleNamespace(namespace=namespace)


def test_flatten_actual_dedupes_and_sorts():
    extraction = {
        "universal_entities": [
            {
                "surface_text": "mayank",
                "entities": [
                    {"entity_id": "mayank", "label": "Mayank", "surface_text": "mayank"}
                ],
            },
        ],
        "regex_entities": [
            {"surface_text": "2026", "rule": "Date"},
        ],
    }

    assert runner.flatten_actual(extraction) == [
        {"surface_text": "2026", "entity_id": "Date"},
        {"surface_text": "mayank", "entity_id": "mayank"},
    ]


def test_flatten_actual_empty():
    assert runner.flatten_actual({"universal_entities": [], "regex_entities": []}) == []


@pytest.mark.parametrize(
    "expected,passed,previous_passed,label",
    [
        (None, None, None, "needs_review"),
        ([{"surface_text": "a", "entity_id": "A"}], True, None, "new"),
        ([{"surface_text": "a", "entity_id": "A"}], True, True, "pass"),
        ([{"surface_text": "a", "entity_id": "A"}], False, True, "regression"),
        ([{"surface_text": "a", "entity_id": "A"}], True, False, "fixed"),
        ([{"surface_text": "a", "entity_id": "A"}], False, False, "fail"),
    ],
)
def test_compute_status_label(expected, passed, previous_passed, label):
    assert runner.compute_status_label(expected, passed, previous_passed) == label


def test_run_test_suite_first_run_labels_new_and_needs_review(conn, monkeypatch):
    store.create_test_case(
        conn,
        "ns1",
        message_text="mayank is here",
        expected=[{"surface_text": "mayank", "entity_id": "mayank"}],
    )
    store.create_test_case(conn, "ns1", message_text="unlabeled query")

    called_texts = []

    def fake_get_surface_texts(bundle, message_text, word_correction=False):
        called_texts.append(message_text)

        if "mayank" in message_text:
            return {
                "universal_entities": [
                    {
                        "surface_text": "mayank",
                        "entities": [
                            {
                                "entity_id": "mayank",
                                "label": "Mayank",
                                "surface_text": "mayank",
                            }
                        ],
                    }
                ],
                "regex_entities": [],
                "no_tag_entities": [],
            }

        return {"universal_entities": [], "regex_entities": [], "no_tag_entities": []}

    monkeypatch.setattr(runner, "get_surface_texts", fake_get_surface_texts)

    summary = runner.run_test_suite(make_bundle("ns1"), conn)

    labels = {r["status_label"] for r in summary["results"]}
    assert labels == {"new", "needs_review"}
    assert summary["accuracy"] == 1.0
    assert summary["graded_count"] == 1
    assert summary["total_count"] == 2
    assert len(called_texts) == 2


def test_run_test_suite_detects_regression(conn, monkeypatch):
    case = store.create_test_case(
        conn,
        "ns1",
        message_text="mayank is here",
        expected=[{"surface_text": "mayank", "entity_id": "mayank"}],
    )

    responses = iter(
        [
            {
                "universal_entities": [
                    {
                        "surface_text": "mayank",
                        "entities": [
                            {
                                "entity_id": "mayank",
                                "label": "Mayank",
                                "surface_text": "mayank",
                            }
                        ],
                    }
                ],
                "regex_entities": [],
                "no_tag_entities": [],
            },
            {"universal_entities": [], "regex_entities": [], "no_tag_entities": []},
        ]
    )

    monkeypatch.setattr(
        runner, "get_surface_texts", lambda *args, **kwargs: next(responses)
    )

    first = runner.run_test_suite(make_bundle("ns1"), conn)
    second = runner.run_test_suite(make_bundle("ns1"), conn)

    assert first["results"][0]["status_label"] == "new"
    assert first["results"][0]["passed"] is True

    assert second["results"][0]["status_label"] == "regression"
    assert second["results"][0]["passed"] is False
    assert second["results"][0]["test_case_id"] == case["id"]


def test_accept_test_case_uses_latest_actual(conn):
    case = store.create_test_case(conn, "ns1", message_text="msg")
    run = store.create_run(conn, "ns1")
    store.create_run_result(
        conn,
        run["id"],
        case["id"],
        [{"surface_text": "a", "entity_id": "A"}],
        None,
        "needs_review",
    )

    accepted = runner.accept_test_case(conn, "ns1", case["id"])

    assert accepted["expected"] == [{"surface_text": "a", "entity_id": "A"}]
    assert accepted["review_status"] == "accepted"


def test_accept_test_case_never_run_raises(conn):
    case = store.create_test_case(conn, "ns1", message_text="msg")

    with pytest.raises(runner.CaseNotRunError):
        runner.accept_test_case(conn, "ns1", case["id"])


def test_reject_test_case_marks_rejected_without_touching_expected(conn):
    case = store.create_test_case(
        conn,
        "ns1",
        message_text="msg",
        expected=[{"surface_text": "a", "entity_id": "A"}],
    )

    rejected = runner.reject_test_case(conn, "ns1", case["id"])

    assert rejected["review_status"] == "rejected"
    assert rejected["expected"] == [{"surface_text": "a", "entity_id": "A"}]
