import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from talkingdb_nel.api import nel


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(nel.router)
    return TestClient(app)


def test_extract_surface_text(client, monkeypatch):
    monkeypatch.setattr(
        nel,
        "get_surface_texts",
        lambda **kwargs: ["New York"],
    )

    response = client.post(
        "/nel/surface-text",
        json={
            "message_text": "I live in New York",
            "word_correction": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == ["New York"]


def test_extract_surface_text_word_correction(client, monkeypatch):
    calls = {}

    def fake(**kwargs):
        calls.update(kwargs)
        return []

    monkeypatch.setattr(nel, "get_surface_texts", fake)

    client.post(
        "/nel/surface-text",
        json={
            "message_text": "abc",
            "word_correction": True,
        },
    )

    assert calls["word_correction"] is True


def test_create_entity(client, monkeypatch):
    payload = {}

    def fake(data):
        payload.update(data)
        return data

    monkeypatch.setattr(nel, "create_entity", fake)

    response = client.post(
        "/nel/entity",
        json={
            "_id": "Q1",
            "label": "Apple",
            "surface_texts": ["apple"],
        },
    )

    assert response.status_code == 200
    assert payload["_id"] == "Q1"
    assert payload["label"] == "Apple"
    assert payload["surface_texts"] == ["apple"]


def test_create_entity_requires_alias(client):
    response = client.post(
        "/nel/entity",
        json={
            "id": "Q1",
        },
    )

    assert response.status_code == 200


def test_add_surface_text(client, monkeypatch):
    calls = {}

    def fake(**kwargs):
        calls.update(kwargs)
        return True

    monkeypatch.setattr(nel, "add_surface_text", fake)

    response = client.put(
        "/nel/surface-text",
        json={
            "entity_id": "Q1",
            "surface_text": "Apple Inc",
        },
    )

    assert response.status_code == 200
    assert calls == {
        "entity_id": "Q1",
        "surface_text": "Apple Inc",
    }


def test_create_fact(client, monkeypatch):
    calls = {}

    def fake(**kwargs):
        calls.update(kwargs)
        return True

    monkeypatch.setattr(nel, "create_fact", fake)

    response = client.post(
        "/nel/fact",
        json={
            "source": "Q1",
            "predicate": "instance_of",
            "target": "Q2",
            "attributes": {
                "rank": 1,
                "confidence": 0.9,
            },
        },
    )

    assert response.status_code == 200
    assert calls == {
        "source": "Q1",
        "predicate": "instance_of",
        "target": "Q2",
        "rank": 1,
        "confidence": 0.9,
    }


def test_create_fact_without_attributes(client, monkeypatch):
    monkeypatch.setattr(nel, "create_fact", lambda **kwargs: kwargs)

    response = client.post(
        "/nel/fact",
        json={
            "source": "A",
            "predicate": "B",
            "target": "C",
        },
    )

    assert response.status_code == 200


def test_create_regex(client, monkeypatch):
    calls = {}

    def fake(**kwargs):
        calls.update(kwargs)
        return True

    monkeypatch.setattr(nel, "create_regex", fake)

    response = client.post(
        "/nel/regex",
        json={
            "entity_id": "Q1",
            "regex": r"\d+",
        },
    )

    assert response.status_code == 200
    assert calls == {
        "entity_id": "Q1",
        "regex": r"\d+",
    }
