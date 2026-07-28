import pytest

from talkingdb_nel.services.lexigraph.extract_surface_text import (
    SurfaceTextExtractor,
)


class FakeWordSpell:
    def lookup(
        self,
        word,
        max_edit_distance,
        least_word_suggestions,
    ):
        return [
            (
                word,
                (100, 0),
            )
        ]


class FakePhraseSuggestion:

    def __init__(self, term):
        self.term = term
        self.entities = [
            {
                "id": "test_entity",
            }
        ]


class FakePhraseSpell:

    def lookup_phrase(
        self,
        phrase,
        max_edit_distance,
    ):
        phrases = {
            "new": [
                FakePhraseSuggestion("new"),
            ],
            "york": [
                FakePhraseSuggestion("york"),
            ],
            "new york": [
                FakePhraseSuggestion("new york"),
            ],
        }

        return phrases.get(
            phrase.lower(),
            [],
        )

    def lookup_exact(
        self,
        phrase,
    ):
        if phrase == "new york":
            return FakePhraseSuggestion(
                "new york"
            )

        if phrase == "new":
            return FakePhraseSuggestion(
                "new"
            )

        return None


@pytest.fixture
def extractor():

    return SurfaceTextExtractor(
        word_spell=FakeWordSpell(),
        phrase_spell=FakePhraseSpell(),
    )


def test_extract_single_word_phrase(
    extractor,
):

    result = extractor.extract(
        "new",
        [],
    )

    assert len(result) == 1

    assert result[0]["corrected_text"] == "new"

    assert result[0]["surface_text"] == "new"

    assert result[0]["index"] == [
        0,
        2,
    ]


def test_extract_two_word_phrase(
    extractor,
):

    result = extractor.extract(
        "new york",
        [],
    )

    matches = [
        item
        for item in result
        if item["corrected_text"] == "new york"
    ]

    assert len(matches) == 1

    assert matches[0]["surface_text"] == "new york"

    assert matches[0]["index"] == [
        0,
        7,
    ]


def test_extract_phrase_with_prefix_text(
    extractor,
):

    result = extractor.extract(
        "hello new york",
        [],
    )

    matches = [
        item
        for item in result
        if item["corrected_text"] == "new york"
    ]

    assert len(matches) == 1

    assert matches[0]["index"] == [
        6,
        13,
    ]

    assert matches[0]["surface_text"] == "new york"


def test_breakpoint_does_not_join_phrase(
    extractor,
):

    result = extractor.extract(
        "new york",
        [
            (
                3,
                1,
            )
        ],
    )

    assert not any(
        item["corrected_text"] == "new york"
        for item in result
    )


def test_preserves_entity_lookup(
    extractor,
):

    result = extractor.extract(
        "new york",
        [],
    )

    match = next(
        item
        for item in result
        if item["corrected_text"] == "new york"
    )

    assert match["entities"] == [
        {
            "id": "test_entity",
        }
    ]


def test_empty_input(
    extractor,
):

    result = extractor.extract(
        "",
        [],
    )

    assert result == []


def test_no_match_returns_empty(
    extractor,
):

    result = extractor.extract(
        "unknown",
        [],
    )

    assert result == []