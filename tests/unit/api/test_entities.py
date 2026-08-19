import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from talkingdb_nel.api import entities
from talkingdb_nel.services.entity.entity import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    SurfaceTextAlreadyExistsError,
)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(entities.router)
    return TestClient(app)


def test_create_entity_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "create_entity",
        lambda **kwargs: {
            "entity_id": kwargs["entity_id"],
            "label": kwargs["label"] or kwargs["entity_id"],
            "surface_texts": kwargs["surface_texts"],
        },
    )

    response = client.post(
        "/entities",
        json={"entity_id": "Q1", "label": "Apple", "surface_texts": ["Apple"]},
    )

    assert response.status_code == 201
    assert response.json() == {
        "entity_id": "Q1",
        "label": "Apple",
        "surface_texts": ["Apple"],
    }


def test_create_entity_conflict(client, monkeypatch):
    def raise_conflict(**kwargs):
        raise EntityAlreadyExistsError(kwargs["entity_id"])

    monkeypatch.setattr(entities, "create_entity", raise_conflict)

    response = client.post("/entities", json={"entity_id": "Q1"})

    assert response.status_code == 409


def test_list_entities(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "list_entities",
        lambda: [{"entity_id": "Q1", "label": "Apple", "surface_texts": ["Apple"]}],
    )

    response = client.get("/entities")

    assert response.status_code == 200
    assert response.json() == [
        {"entity_id": "Q1", "label": "Apple", "surface_texts": ["Apple"]}
    ]


def test_get_entity_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "get_entity",
        lambda entity_id: {
            "entity_id": entity_id,
            "label": "Apple",
            "surface_texts": ["Apple"],
        },
    )

    response = client.get("/entities/Q1")

    assert response.status_code == 200
    assert response.json()["entity_id"] == "Q1"


def test_get_entity_not_found(client, monkeypatch):
    monkeypatch.setattr(entities, "get_entity", lambda entity_id: None)

    response = client.get("/entities/Q1")

    assert response.status_code == 404


def test_add_surface_text_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "add_surface_text",
        lambda **kwargs: {
            "entity_id": kwargs["entity_id"],
            "label": "Apple",
            "surface_texts": ["Apple", kwargs["surface_text"]],
        },
    )

    response = client.post(
        "/entities/Q1/surface-texts",
        json={"surface_text": "Apple Inc"},
    )

    assert response.status_code == 201
    assert response.json()["surface_texts"] == ["Apple", "Apple Inc"]


def test_add_surface_text_entity_not_found(client, monkeypatch):
    def raise_not_found(**kwargs):
        raise EntityNotFoundError(kwargs["entity_id"])

    monkeypatch.setattr(entities, "add_surface_text", raise_not_found)

    response = client.post(
        "/entities/Q1/surface-texts",
        json={"surface_text": "Apple Inc"},
    )

    assert response.status_code == 404


def test_add_surface_text_duplicate(client, monkeypatch):
    def raise_conflict(**kwargs):
        raise SurfaceTextAlreadyExistsError(kwargs["surface_text"])

    monkeypatch.setattr(entities, "add_surface_text", raise_conflict)

    response = client.post(
        "/entities/Q1/surface-texts",
        json={"surface_text": "Apple"},
    )

    assert response.status_code == 409


def test_add_regex_rule_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "create_regex",
        lambda **kwargs: {"entity_id": kwargs["entity_id"], "regex": kwargs["regex"]},
    )

    response = client.post(
        "/entities/Date/regex-rules",
        json={"regex": r"\d{4}"},
    )

    assert response.status_code == 201
    assert response.json() == {"entity_id": "Date", "regex": r"\d{4}"}


def test_add_regex_rule_entity_not_found(client, monkeypatch):
    def raise_not_found(**kwargs):
        raise EntityNotFoundError(kwargs["entity_id"])

    monkeypatch.setattr(entities, "create_regex", raise_not_found)

    response = client.post(
        "/entities/Date/regex-rules",
        json={"regex": r"\d{4}"},
    )

    assert response.status_code == 404
