import pytest

from talkingdb_nel.services.entity import entity


@pytest.fixture(autouse=True)
def reset_mocks(monkeypatch):
    monkeypatch.setattr(entity.entity_model, "add_entity", lambda **kwargs: None)
    monkeypatch.setattr(entity.entity_model, "has_entity", lambda entity_id: False)
    monkeypatch.setattr(entity.entity_model, "get_entity", lambda entity_id: None)
    monkeypatch.setattr(
        entity.entity_model, "update_surface_texts", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(entity.entity_model, "add_fact", lambda **kwargs: "fact-1")

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
        "entity_id": "Q1",
        "surface_texts": ["Apple", "Apple Inc"],
    }

    entity.index_entity(e)

    assert word_loaded == [e]
    assert phrase_loaded == [e]


def test_create_entity_success():
    result = entity.create_entity(
        "Q1",
        label="Apple",
        surface_texts=["Apple", "Apple Inc"],
    )

    assert result == {
        "entity_id": "Q1",
        "label": "Apple",
        "surface_texts": ["Apple", "Apple Inc"],
    }


def test_create_entity_defaults_label_to_entity_id():
    result = entity.create_entity("Q1")

    assert result == {
        "entity_id": "Q1",
        "label": "Q1",
        "surface_texts": [],
    }


def test_create_entity_already_exists(monkeypatch):
    monkeypatch.setattr(entity.entity_model, "has_entity", lambda entity_id: True)

    with pytest.raises(entity.EntityAlreadyExistsError):
        entity.create_entity("Q1")


def test_get_entity_found(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "get_entity",
        lambda entity_id: {
            "id": entity_id,
            "label": "Apple",
            "surface_texts": ["Apple"],
        },
    )

    assert entity.get_entity("Q1") == {
        "entity_id": "Q1",
        "label": "Apple",
        "surface_texts": ["Apple"],
    }


def test_get_entity_missing():
    assert entity.get_entity("Q1") is None


def test_list_entities(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "iter_entities",
        lambda: iter(
            [
                {"id": "Q1", "label": "Apple", "surface_texts": ["Apple"]},
                {"id": "Q2", "label": "Google", "surface_texts": ["Google"]},
            ]
        ),
    )

    assert entity.list_entities() == [
        {"entity_id": "Q1", "label": "Apple", "surface_texts": ["Apple"]},
        {"entity_id": "Q2", "label": "Google", "surface_texts": ["Google"]},
    ]


def test_add_surface_text_success(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "get_entity",
        lambda _: {
            "label": "Apple",
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

    assert result == {
        "entity_id": "Q1",
        "label": "Apple",
        "surface_texts": ["Apple", "Apple Inc"],
    }

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

    with pytest.raises(entity.EntityNotFoundError):
        entity.add_surface_text("Q1", "Apple")


def test_add_surface_text_duplicate(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "get_entity",
        lambda _: {
            "label": "Apple",
            "surface_texts": ["Apple"],
        },
    )

    with pytest.raises(entity.SurfaceTextAlreadyExistsError):
        entity.add_surface_text("Q1", "Apple")


def test_create_fact(monkeypatch):
    called = {}

    monkeypatch.setattr(
        entity.entity_model,
        "add_fact",
        lambda **kwargs: called.update(kwargs) or "fact-42",
    )

    result = entity.create_fact(
        "A",
        "KNOWS",
        "B",
        since=2025,
    )

    assert result == {
        "id": "fact-42",
        "source": "A",
        "target": "B",
        "predicate": "KNOWS",
        "since": 2025,
    }

    assert called["source"] == "A"
    assert called["target"] == "B"
    assert called["predicate"] == "KNOWS"
    assert called["since"] == 2025


def test_get_fact_found(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "get_fact",
        lambda fact_id: {
            "id": fact_id,
            "source": "A",
            "target": "B",
            "predicate": "KNOWS",
        },
    )

    assert entity.get_fact("fact-1") == {
        "id": "fact-1",
        "source": "A",
        "target": "B",
        "predicate": "KNOWS",
    }


def test_get_fact_missing(monkeypatch):
    monkeypatch.setattr(entity.entity_model, "get_fact", lambda fact_id: None)

    assert entity.get_fact("fact-1") is None


def test_list_facts(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "iter_facts",
        lambda: iter(
            [
                {"id": "fact-1", "source": "A", "target": "B", "predicate": "KNOWS"},
            ]
        ),
    )

    assert entity.list_facts() == [
        {"id": "fact-1", "source": "A", "target": "B", "predicate": "KNOWS"},
    ]


def test_suggestion_parts_tuple():
    assert entity._suggestion_parts(("apple", (3, 1))) == ("apple", 1)


def test_resolve_entities_deduplicates_by_entity_id(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "get_entities_by_surface_text",
        lambda text: [
            {"id": "Q1", "label": "Apple", "surface_texts": ["Apple"]},
            {"id": "Q1", "label": "Apple", "surface_texts": ["Apple"]},
        ],
    )

    resolved = entity._resolve_entities([("apple", (1, 0))])

    assert resolved == [
        {"entity_id": "Q1", "label": "Apple", "surface_text": "apple"},
    ]


def test_resolve_entities_no_match(monkeypatch):
    monkeypatch.setattr(
        entity.entity_model,
        "get_entities_by_surface_text",
        lambda text: [],
    )

    assert entity._resolve_entities([("apple", (1, 0))]) == []


def test_get_surface_texts_attaches_entity_id_and_drops_unresolved(monkeypatch):
    monkeypatch.setattr(
        entity.surface_text_extractor,
        "extract",
        lambda *args, **kwargs: [
            {
                "index": [0, 4],
                "surface_text": "apple",
                "corrected_text": "apple",
                "score": 0,
                "entities": [("apple", (1, 0))],
            },
            {
                "index": [10, 15],
                "surface_text": "mango",
                "corrected_text": "mango",
                "score": 0,
                "entities": [("mango", (1, 0))],
            },
        ],
    )

    monkeypatch.setattr(
        entity.entity_model,
        "get_entities_by_surface_text",
        lambda text: (
            [{"id": "Q1", "label": "Apple", "surface_texts": ["apple"]}]
            if text == "apple"
            else []
        ),
    )

    result = entity.get_surface_texts("apple mango", word_correction=False)

    assert len(result["universal_entities"]) == 1
    assert result["universal_entities"][0]["entities"] == [
        {"entity_id": "Q1", "label": "Apple", "surface_text": "apple"},
    ]


def test_iter_no_tag_windows_builds_multi_word_windows():
    message_text = "satyam gpta is here"
    no_tags = [
        {"index": [0, 5]},
        {"index": [7, 10]},
        {"index": [12, 13]},
        {"index": [15, 18]},
    ]

    windows = list(entity._iter_no_tag_windows(message_text, no_tags))

    assert (0, 5, "satyam") in windows
    assert (7, 10, "gpta") in windows
    assert (0, 10, "satyam gpta") in windows


def test_iter_no_tag_windows_stops_at_non_whitespace_gap():
    message_text = "satyam.gpta"
    no_tags = [
        {"index": [0, 5]},
        {"index": [7, 10]},
    ]

    windows = list(entity._iter_no_tag_windows(message_text, no_tags))

    assert (0, 10, "satyam.gpta") not in windows
    assert (0, 5, "satyam") in windows
    assert (7, 10, "gpta") in windows


def test_find_fuzzy_matches(monkeypatch):
    monkeypatch.setattr(
        entity.phrase_matcher,
        "get_suggestions",
        lambda text, max_edit_distance=None: (
            [("mayank", (3, 1))] if text == "myank" else []
        ),
    )
    monkeypatch.setattr(
        entity.entity_model,
        "get_entities_by_surface_text",
        lambda text: (
            [{"id": "Q1", "label": "Mayank", "surface_texts": ["mayank"]}]
            if text == "mayank"
            else []
        ),
    )

    message_text = "myank is here"
    no_tags = [
        {"index": [0, 4]},
        {"index": [6, 7]},
        {"index": [9, 12]},
    ]

    matches = list(entity._find_fuzzy_matches(message_text, no_tags))

    assert matches == [
        {
            "index": [0, 4],
            "surface_text": "myank",
            "corrected_text": "mayank",
            "score": -1,
            "entities": [
                {"entity_id": "Q1", "label": "Mayank", "surface_text": "mayank"}
            ],
        }
    ]


def test_get_surface_texts_word_correction_flag_gates_fuzzy_matches(monkeypatch):
    monkeypatch.setattr(
        entity.lemmatizer,
        "lemmatize",
        lambda no_tags: (no_tags, []),
    )
    monkeypatch.setattr(
        entity.phrase_matcher,
        "get_suggestions",
        lambda text, max_edit_distance=None: (
            [("mayank", (3, 1))]
            if text == "myank" and (max_edit_distance or 0) >= 1
            else []
        ),
    )
    monkeypatch.setattr(
        entity.entity_model,
        "get_entities_by_surface_text",
        lambda text: (
            [{"id": "Q1", "label": "Mayank", "surface_texts": ["mayank"]}]
            if text == "mayank"
            else []
        ),
    )

    result_off = entity.get_surface_texts("myank is here", word_correction=False)
    assert result_off["universal_entities"] == []

    result_on = entity.get_surface_texts("myank is here", word_correction=True)
    assert len(result_on["universal_entities"]) == 1
    assert result_on["universal_entities"][0]["corrected_text"] == "mayank"
    assert result_on["universal_entities"][0]["entities"] == [
        {"entity_id": "Q1", "label": "Mayank", "surface_text": "mayank"}
    ]

    no_tag_texts = [tag["surface_text"] for tag in result_on["no_tag_entities"]]
    assert "myank" not in no_tag_texts
    assert no_tag_texts == ["is", "here"]


def test_create_regex_success(monkeypatch):
    called = []

    monkeypatch.setattr(entity.entity_model, "has_entity", lambda entity_id: True)
    monkeypatch.setattr(
        entity.regex_model,
        "add_rule",
        lambda entity_id, regex: called.append((entity_id, regex)),
    )
    monkeypatch.setattr(entity.regex_model, "save", lambda conn: None)

    result = entity.create_regex(
        "Date",
        r"\d{4}",
    )

    assert result == {"entity_id": "Date", "regex": r"\d{4}"}
    assert called == [("Date", r"\d{4}")]


def test_create_regex_missing_entity(monkeypatch):
    monkeypatch.setattr(entity.entity_model, "has_entity", lambda entity_id: False)

    with pytest.raises(entity.EntityNotFoundError):
        entity.create_regex("Date", r"\d{4}")
