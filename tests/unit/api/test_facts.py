import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from talkingdb_nel.api import facts


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(facts.router)
    return TestClient(app)


def test_create_fact_success(client, monkeypatch):
    monkeypatch.setattr(
        facts,
        "create_fact",
        lambda source, predicate, target, **attributes: {
            "id": "fact-1",
            "source": source,
            "target": target,
            "predicate": predicate,
            **attributes,
        },
    )

    response = client.post(
        "/facts",
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
        lambda: [{"id": "fact-1", "source": "A", "target": "B", "predicate": "KNOWS"}],
    )

    response = client.get("/facts")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "fact-1", "source": "A", "target": "B", "predicate": "KNOWS"}
    ]


def test_get_fact_success(client, monkeypatch):
    monkeypatch.setattr(
        facts,
        "get_fact",
        lambda fact_id: {
            "id": fact_id,
            "source": "A",
            "target": "B",
            "predicate": "KNOWS",
        },
    )

    response = client.get("/facts/fact-1")

    assert response.status_code == 200
    assert response.json()["id"] == "fact-1"


def test_get_fact_not_found(client, monkeypatch):
    monkeypatch.setattr(facts, "get_fact", lambda fact_id: None)

    response = client.get("/facts/fact-1")

    assert response.status_code == 404
