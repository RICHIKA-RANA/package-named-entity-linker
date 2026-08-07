import pytest

from talkingdb_nel.services.entity import entity


@pytest.fixture(autouse=True)
def reset_mocks(monkeypatch):
    monkeypatch.setattr(entity.entity_model, "add_entity", lambda **kwargs: None)
    monkeypatch.setattr(entity.entity_model, "get_entity", lambda entity_id: None)
    monkeypatch.setattr(
        entity.entity_model, "update_surface_texts", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(entity.entity_model, "add_fact", lambda **kwargs: None)

    monkeypatch.setattr(
        entity.word_matcher,
        "load",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        entity.phrase_matcher,
        "load",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(entity.regex_controller, "process", lambda text: [])
    monkeypatch.setattr(
        entity.surface_text_extractor, "extract", lambda *args, **kwargs: []
    )


def test_index_entity(monkeypatch):
    word_loaded = []
    phrase_loaded = []

    monkeypatch.setattr(
        entity.word_matcher,
        "load",
        lambda docs: word_loaded.extend(docs),
    )

    monkeypatch.setattr(
        entity.phrase_matcher,
        "load",
        lambda docs: phrase_loaded.extend(docs),
    )

    e = {
        "_id": "Q1",
        "surface_texts": ["Apple", "Apple Inc"],
    }

    entity.index_entity(e)

    assert word_loaded == [e]
    assert phrase_loaded == [e]


def test_add_surface_text_success(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "get_entity",
        lambda _: {
            "surface_texts": ["Apple"],
        },
    )

    updated = {}

    monkeypatch.setattr(
        entity.entity_model,
        "update_surface_texts",
        lambda entity_id, texts: updated.update(
            {
                "id": entity_id,
                "texts": texts,
            }
        ),
    )

    result = entity.add_surface_text(
        "Q1",
        "Apple Inc",
    )

    assert result["success"]

    assert updated["texts"] == [
        "Apple",
        "Apple Inc",
    ]


def test_add_surface_text_missing_entity(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "get_entity",
        lambda _: None,
    )

    result = entity.add_surface_text(
        "Q1",
        "Apple",
    )

    assert result == {
        "success": False,
        "message": "Entity not found",
    }


def test_add_surface_text_duplicate(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "get_entity",
        lambda _: {
            "surface_texts": ["Apple"],
        },
    )

    result = entity.add_surface_text(
        "Q1",
        "Apple",
    )

    assert result == {
        "success": False,
        "message": "Already exists",
    }


def test_create_fact(monkeypatch):
    called = {}

    monkeypatch.setattr(
        entity.entity_model,
        "add_fact",
        lambda **kwargs: called.update(kwargs),
    )

    result = entity.create_fact(
        "A",
        "KNOWS",
        "B",
        since=2025,
    )

    assert result == {"success": True}

    assert called["source"] == "A"
    assert called["target"] == "B"
    assert called["predicate"] == "KNOWS"
    assert called["since"] == 2025


def test_create_regex(monkeypatch):
    called = []

    monkeypatch.setattr(
        entity.regex_model,
        "add_rule",
        lambda entity_id, regex: called.append((entity_id, regex)),
    )

    result = entity.create_regex(
        "Date",
        r"\d{4}",
    )

    assert result == {"success": True}

    assert called == [("Date", r"\d{4}")]
