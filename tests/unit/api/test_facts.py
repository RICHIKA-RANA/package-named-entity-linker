import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from talkingdb_nel.api import facts
from talkingdb_nel.api.dependencies import get_namespace_bundle
from talkingdb_nel.services.entity.entity import FactNotFoundError

NS = "test-ns"


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(facts.router)
    app.dependency_overrides[get_namespace_bundle] = lambda: object()
    return TestClient(app)


def test_create_fact_success(client, monkeypatch):
    monkeypatch.setattr(
        facts,
        "create_fact",
        lambda bundle, source, predicate, target, **attributes: {
            "id": "fact-1",
            "source": source,
            "target": target,
            "predicate": predicate,
            **attributes,
        },
    )

    response = client.post(
        f"/api/namespaces/{NS}/facts",
        json={
            "source": "A",
            "predicate": "KNOWS",
            "target": "B",
            "attributes": {"since": 2025},
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": "fact-1",
        "source": "A",
        "target": "B",
        "predicate": "KNOWS",
        "since": 2025,
    }


def test_list_facts(client, monkeypatch):
    monkeypatch.setattr(
        facts,
        "list_facts",
        lambda bundle: [
            {"id": "fact-1", "source": "A", "target": "B", "predicate": "KNOWS"}
        ],
    )

    response = client.get(f"/api/namespaces/{NS}/facts")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "fact-1", "source": "A", "target": "B", "predicate": "KNOWS"}
    ]


def test_get_fact_success(client, monkeypatch):
    monkeypatch.setattr(
        facts,
        "get_fact",
        lambda bundle, fact_id: {
            "id": fact_id,
            "source": "A",
            "target": "B",
            "predicate": "KNOWS",
        },
    )

    response = client.get(f"/api/namespaces/{NS}/facts/fact-1")

    assert response.status_code == 200
    assert response.json()["id"] == "fact-1"


def test_get_fact_not_found(client, monkeypatch):
    monkeypatch.setattr(facts, "get_fact", lambda bundle, fact_id: None)

    response = client.get(f"/api/namespaces/{NS}/facts/fact-1")

    assert response.status_code == 404


def test_update_fact_success(client, monkeypatch):
    monkeypatch.setattr(
        facts,
        "update_fact",
        lambda bundle, **kwargs: {
            "id": kwargs["fact_id"],
            "source": "A",
            "target": "B",
            "predicate": kwargs["predicate"],
        },
    )

    response = client.patch(
        f"/api/namespaces/{NS}/facts/fact-1",
        json={"predicate": "WORKS_WITH"},
    )

    assert response.status_code == 200
    assert response.json()["predicate"] == "WORKS_WITH"


def test_update_fact_not_found(client, monkeypatch):
    def raise_not_found(bundle, **kwargs):
        raise FactNotFoundError(kwargs["fact_id"])

    monkeypatch.setattr(facts, "update_fact", raise_not_found)

    response = client.patch(
        f"/api/namespaces/{NS}/facts/fact-1",
        json={"predicate": "WORKS_WITH"},
    )

    assert response.status_code == 404


def test_delete_fact_success(client, monkeypatch):
    called = []

    monkeypatch.setattr(
        facts, "delete_fact", lambda bundle, **kwargs: called.append(kwargs["fact_id"])
    )

    response = client.delete(f"/api/namespaces/{NS}/facts/fact-1")

    assert response.status_code == 204
    assert called == ["fact-1"]


def test_delete_fact_not_found(client, monkeypatch):
    def raise_not_found(bundle, **kwargs):
        raise FactNotFoundError(kwargs["fact_id"])

    monkeypatch.setattr(facts, "delete_fact", raise_not_found)

    response = client.delete(f"/api/namespaces/{NS}/facts/fact-1")

    assert response.status_code == 404
