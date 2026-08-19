from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from talkingdb_nel.api import testsuite
from talkingdb_nel.api.dependencies import get_namespace_bundle
from talkingdb_nel.services.testsuite import store
from talkingdb_nel.services.testsuite.runner import CaseNotRunError

NS = "test-ns"


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(testsuite.router)
    app.dependency_overrides[get_namespace_bundle] = lambda: SimpleNamespace(
        namespace=NS, entity_conn=None
    )
    return TestClient(app)


def test_create_test_case_success(client, monkeypatch):
    monkeypatch.setattr(
        testsuite.store,
        "create_test_case",
        lambda conn, namespace, **kwargs: {
            "id": "tc-1",
            "namespace": namespace,
            "message_text": kwargs["message_text"],
            "word_correction": kwargs["word_correction"],
            "expected": kwargs["expected"],
            "review_status": "pending",
            "created_at": "2026-01-01T00:00:00+00:00",
        },
    )

    response = client.post(
        f"/api/namespaces/{NS}/test-cases",
        json={
            "message_text": "hi mayank",
            "expected": [{"surface_text": "mayank", "entity_id": "mayank"}],
        },
    )

    assert response.status_code == 201
    assert response.json()["expected"] == [
        {"surface_text": "mayank", "entity_id": "mayank"}
    ]


def test_bulk_upload_test_cases(client, monkeypatch):
    monkeypatch.setattr(
        testsuite,
        "bulk_create_test_cases",
        lambda conn, namespace, format, content: {"created": 2, "errors": []},
    )

    response = client.post(
        f"/api/namespaces/{NS}/test-cases/bulk",
        json={"format": "json", "content": "[]"},
    )

    assert response.status_code == 200
    assert response.json() == {"created": 2, "errors": []}


def test_list_test_cases(client, monkeypatch):
    monkeypatch.setattr(
        testsuite.store,
        "list_test_cases",
        lambda conn, namespace: [
            {
                "id": "tc-1",
                "namespace": namespace,
                "message_text": "hi",
                "word_correction": False,
                "expected": None,
                "review_status": "pending",
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ],
    )

    response = client.get(f"/api/namespaces/{NS}/test-cases")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "tc-1"


def test_update_test_case_success(client, monkeypatch):
    captured = {}

    def fake_update(conn, namespace, test_case_id, **kwargs):
        captured.update(kwargs)
        return {
            "id": test_case_id,
            "namespace": namespace,
            "message_text": kwargs.get("message_text", "hi"),
            "word_correction": False,
            "expected": kwargs.get("expected"),
            "review_status": kwargs.get("review_status", "pending"),
            "created_at": "2026-01-01T00:00:00+00:00",
        }

    monkeypatch.setattr(testsuite.store, "update_test_case", fake_update)

    response = client.patch(
        f"/api/namespaces/{NS}/test-cases/tc-1", json={"review_status": "accepted"}
    )

    assert response.status_code == 200
    assert response.json()["review_status"] == "accepted"
    assert captured == {"review_status": "accepted"}


def test_update_test_case_not_found(client, monkeypatch):
    def raise_not_found(conn, namespace, test_case_id, **kwargs):
        raise store.TestCaseNotFoundError(test_case_id)

    monkeypatch.setattr(testsuite.store, "update_test_case", raise_not_found)

    response = client.patch(
        f"/api/namespaces/{NS}/test-cases/tc-1", json={"review_status": "accepted"}
    )

    assert response.status_code == 404


def test_delete_test_case_success(client, monkeypatch):
    called = []

    monkeypatch.setattr(
        testsuite.store,
        "delete_test_case",
        lambda conn, namespace, test_case_id: called.append(test_case_id),
    )

    response = client.delete(f"/api/namespaces/{NS}/test-cases/tc-1")

    assert response.status_code == 204
    assert called == ["tc-1"]


def test_delete_test_case_not_found(client, monkeypatch):
    def raise_not_found(conn, namespace, test_case_id):
        raise store.TestCaseNotFoundError(test_case_id)

    monkeypatch.setattr(testsuite.store, "delete_test_case", raise_not_found)

    response = client.delete(f"/api/namespaces/{NS}/test-cases/tc-1")

    assert response.status_code == 404


def test_accept_test_case_success(client, monkeypatch):
    monkeypatch.setattr(
        testsuite,
        "accept_test_case",
        lambda conn, namespace, test_case_id: {
            "id": test_case_id,
            "namespace": namespace,
            "message_text": "hi",
            "word_correction": False,
            "expected": [{"surface_text": "a", "entity_id": "A"}],
            "review_status": "accepted",
            "created_at": "2026-01-01T00:00:00+00:00",
        },
    )

    response = client.post(f"/api/namespaces/{NS}/test-cases/tc-1/accept")

    assert response.status_code == 200
    assert response.json()["review_status"] == "accepted"


def test_accept_test_case_never_run(client, monkeypatch):
    def raise_not_run(conn, namespace, test_case_id):
        raise CaseNotRunError(test_case_id)

    monkeypatch.setattr(testsuite, "accept_test_case", raise_not_run)

    response = client.post(f"/api/namespaces/{NS}/test-cases/tc-1/accept")

    assert response.status_code == 409


def test_reject_test_case_success(client, monkeypatch):
    monkeypatch.setattr(
        testsuite,
        "reject_test_case",
        lambda conn, namespace, test_case_id: {
            "id": test_case_id,
            "namespace": namespace,
            "message_text": "hi",
            "word_correction": False,
            "expected": None,
            "review_status": "rejected",
            "created_at": "2026-01-01T00:00:00+00:00",
        },
    )

    response = client.post(f"/api/namespaces/{NS}/test-cases/tc-1/reject")

    assert response.status_code == 200
    assert response.json()["review_status"] == "rejected"


def test_create_test_run(client, monkeypatch):
    monkeypatch.setattr(
        testsuite,
        "run_test_suite",
        lambda bundle, conn, triggering_commit_id: {
            "run": {
                "id": "run-1",
                "namespace": NS,
                "created_at": "2026-01-01T00:00:00+00:00",
                "triggering_commit_id": triggering_commit_id,
            },
            "results": [],
            "accuracy": None,
            "graded_count": 0,
            "passed_count": 0,
            "total_count": 0,
        },
    )

    response = client.post(f"/api/namespaces/{NS}/test-runs", json={})

    assert response.status_code == 201
    assert response.json()["run"]["id"] == "run-1"


def test_list_test_runs(client, monkeypatch):
    monkeypatch.setattr(
        testsuite.store,
        "list_runs",
        lambda conn, namespace: [
            {
                "id": "run-1",
                "namespace": namespace,
                "created_at": "2026-01-01T00:00:00+00:00",
                "triggering_commit_id": None,
            }
        ],
    )

    response = client.get(f"/api/namespaces/{NS}/test-runs")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "run-1"


def test_get_test_run_results(client, monkeypatch):
    monkeypatch.setattr(
        testsuite.store,
        "list_run_results",
        lambda conn, run_id: [
            {
                "id": "result-1",
                "run_id": run_id,
                "test_case_id": "tc-1",
                "actual": [{"surface_text": "a", "entity_id": "A"}],
                "passed": True,
                "status_label": "pass",
            }
        ],
    )

    response = client.get(f"/api/namespaces/{NS}/test-runs/run-1")

    assert response.status_code == 200
    assert response.json()[0]["status_label"] == "pass"
