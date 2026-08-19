from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from talkingdb_nel.api import namespaces
from talkingdb_nel.api.dependencies import get_namespace_bundle
from talkingdb_nel.services.namespace import store

NS = "test-ns"


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(namespaces.router)
    app.dependency_overrides[get_namespace_bundle] = lambda: SimpleNamespace(
        namespace=NS,
        entity_model=SimpleNamespace(
            g_json=lambda: {
                "directed": True,
                "multigraph": True,
                "graph": {},
                "nodes": [],
                "edges": [],
            }
        ),
    )
    return TestClient(app)


def test_create_namespace_success(client, monkeypatch):
    monkeypatch.setattr(
        namespaces.store,
        "create_namespace",
        lambda conn, name, description: {
            "name": name,
            "description": description,
            "created_at": "2026-01-01T00:00:00+00:00",
        },
    )

    response = client.post(
        "/namespaces",
        json={"name": NS, "description": "a test namespace"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == NS


def test_create_namespace_conflict(client, monkeypatch):
    def raise_conflict(conn, name, description):
        raise store.NamespaceAlreadyExistsError(name)

    monkeypatch.setattr(namespaces.store, "create_namespace", raise_conflict)

    response = client.post("/namespaces", json={"name": NS})

    assert response.status_code == 409


def test_list_namespaces(client, monkeypatch):
    monkeypatch.setattr(
        namespaces.store,
        "list_namespaces",
        lambda conn: [
            {"name": NS, "description": None, "created_at": "2026-01-01T00:00:00+00:00"}
        ],
    )

    response = client.get("/namespaces")

    assert response.status_code == 200
    assert response.json()[0]["name"] == NS


def test_get_namespace_not_found(client, monkeypatch):
    monkeypatch.setattr(namespaces.store, "get_namespace", lambda conn, name: None)

    response = client.get(f"/namespaces/{NS}")

    assert response.status_code == 404


def test_create_commit(client, monkeypatch):
    monkeypatch.setattr(
        namespaces,
        "commit_namespace",
        lambda bundle, message: {
            "commit_id": "c1",
            "parent_commit_id": None,
            "message": message,
            "created_at": "2026-01-01T00:00:00+00:00",
        },
    )

    response = client.post(f"/namespaces/{NS}/commits", json={"message": "initial"})

    assert response.status_code == 201
    assert response.json()["message"] == "initial"


def test_list_commits(client, monkeypatch):
    monkeypatch.setattr(
        namespaces.store,
        "list_commits",
        lambda conn, namespace: [
            {
                "commit_id": "c1",
                "parent_commit_id": None,
                "message": "initial",
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ],
    )

    response = client.get(f"/namespaces/{NS}/commits")

    assert response.status_code == 200
    assert response.json()[0]["commit_id"] == "c1"


def test_get_commit_not_found(client, monkeypatch):
    monkeypatch.setattr(
        namespaces.store, "get_commit", lambda conn, namespace, commit_id: None
    )

    response = client.get(f"/namespaces/{NS}/commits/nonexistent")

    assert response.status_code == 404


def test_rollback_success(client, monkeypatch):
    monkeypatch.setattr(
        namespaces,
        "rollback_namespace",
        lambda bundle, commit_id: {
            "commit_id": "c2",
            "parent_commit_id": commit_id,
            "message": f"Rollback to {commit_id}",
            "created_at": "2026-01-01T00:00:00+00:00",
        },
    )

    response = client.post(f"/namespaces/{NS}/commits/c1/rollback")

    assert response.status_code == 201
    assert response.json()["message"] == "Rollback to c1"


def test_rollback_commit_not_found(client, monkeypatch):
    def raise_not_found(bundle, commit_id):
        raise store.CommitNotFoundError(commit_id)

    monkeypatch.setattr(namespaces, "rollback_namespace", raise_not_found)

    response = client.post(f"/namespaces/{NS}/commits/nonexistent/rollback")

    assert response.status_code == 404


def test_get_graph(client):
    response = client.get(f"/namespaces/{NS}/graph")

    assert response.status_code == 200
    assert response.json() == {
        "directed": True,
        "multigraph": True,
        "nodes": [],
        "edges": [],
    }
