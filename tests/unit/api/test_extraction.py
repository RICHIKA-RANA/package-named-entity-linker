import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from talkingdb_nel.api import extraction


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(extraction.router)
    return TestClient(app)


def test_create_extraction(client, monkeypatch):
    monkeypatch.setattr(
        extraction,
        "get_surface_texts",
        lambda **kwargs: {
            "universal_entities": [
                {
                    "index": [0, 5],
                    "surface_text": "apple",
                    "corrected_text": "apple",
                    "score": 0,
                    "entities": [
                        {
                            "entity_id": "Q1",
                            "label": "Apple",
                            "surface_text": "apple",
                        }
                    ],
                }
            ],
            "regex_entities": [],
            "no_tag_entities": [],
        },
    )

    response = client.post(
        "/extractions",
        json={"message_text": "I like Apple", "word_correction": False},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["universal_entities"][0]["entities"][0]["entity_id"] == "Q1"
    assert body["regex_entities"] == []
    assert body["no_tag_entities"] == []


def test_create_extraction_passes_word_correction_flag(client, monkeypatch):
    calls = {}

    def fake(**kwargs):
        calls.update(kwargs)
        return {"universal_entities": [], "regex_entities": [], "no_tag_entities": []}

    monkeypatch.setattr(extraction, "get_surface_texts", fake)

    client.post(
        "/extractions",
        json={"message_text": "hello", "word_correction": True},
    )

    assert calls == {"message_text": "hello", "word_correction": True}
