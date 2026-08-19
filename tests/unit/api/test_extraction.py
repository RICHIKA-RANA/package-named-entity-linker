import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from talkingdb_nel.api import extraction
from talkingdb_nel.api.dependencies import get_namespace_bundle

NS = "test-ns"


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(extraction.router)
    app.dependency_overrides[get_namespace_bundle] = lambda: object()
    return TestClient(app)


def test_create_extraction(client, monkeypatch):
    monkeypatch.setattr(
        extraction,
        "get_surface_texts",
        lambda bundle, **kwargs: {
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
        f"/api/namespaces/{NS}/extractions",
        json={"message_text": "I like Apple", "word_correction": False},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["universal_entities"][0]["entities"][0]["entity_id"] == "Q1"
    assert body["regex_entities"] == []
    assert body["no_tag_entities"] == []


def test_create_extraction_passes_word_correction_flag(client, monkeypatch):
    calls = {}

    def fake(bundle, **kwargs):
        calls.update(kwargs)
        return {"universal_entities": [], "regex_entities": [], "no_tag_entities": []}

    monkeypatch.setattr(extraction, "get_surface_texts", fake)

    client.post(
        f"/api/namespaces/{NS}/extractions",
        json={"message_text": "hello", "word_correction": True},
    )

    assert calls == {"message_text": "hello", "word_correction": True}
