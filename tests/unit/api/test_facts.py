import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from talkingdb_nel.api import facts
from talkingdb_nel.api.dependencies import get_namespace_bundle

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
        f"/namespaces/{NS}/facts",
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

    response = client.get(f"/namespaces/{NS}/facts")

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

    response = client.get(f"/namespaces/{NS}/facts/fact-1")

    assert response.status_code == 200
    assert response.json()["id"] == "fact-1"


def test_get_fact_not_found(client, monkeypatch):
    monkeypatch.setattr(facts, "get_fact", lambda bundle, fact_id: None)

    response = client.get(f"/namespaces/{NS}/facts/fact-1")

    assert response.status_code == 404
