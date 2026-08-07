import pytest

from talkingdb_nel.services.lexigraph.extractor import (
    SurfaceTextExtractor,
)


class FakeWordSpell:
    def get_suggestions(
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
    def __init__(self):
        self._phrases = {
            "new": FakePhraseSuggestion("new"),
            "york": FakePhraseSuggestion("york"),
            "new york": FakePhraseSuggestion("new york"),
            "very": FakePhraseSuggestion("very"),
            "good": FakePhraseSuggestion("good"),
            "very good": FakePhraseSuggestion("very good"),
        }

    def get_suggestions(
        self,
        phrase,
        max_edit_distance=None,
    ):
        phrase = phrase.lower()

        if phrase not in self._phrases:
            return []

        # Match SentenceSymSpell API:
        # (surface_text, (frequency, edit_distance))
        return [
            (
                phrase,
                (
                    100,
                    0,
                ),
            )
        ]

    def lookup_exact(
        self,
        phrase,
    ):
        return self._phrases.get(
            phrase.lower()
        )


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

    assert match["entities"] == [('new york', (100, 0))]


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


def test_word_correction_disabled(
    extractor,
):

    result = extractor.extract(
        "nwe york",
        [],
        word_correction=False,
    )

    assert not any(
        item["corrected_text"] == "new york"
        for item in result
    )


def test_phrase_expires_after_large_gap(
    extractor,
):

    result = extractor.extract(
        "new hello hello hello hello york",
        [],
    )

    assert not any(
        item["corrected_text"] == "new york"
        for item in result
    )


def test_case_insensitive(
    extractor,
):

    result = extractor.extract(
        "NEW YORK",
        [],
    )

    assert any(
        item["corrected_text"] == "new york"
        for item in result
    )


def test_duplicate_phrase_not_returned_twice(
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


def test_repeated_words(
    extractor,
):

    result = extractor.extract(
        "very very good",
        [],
    )

    matches = [
        item
        for item in result
        if item["corrected_text"] == "very good"
    ]

    assert len(matches) == 1


def test_overlapping_phrases(
    extractor,
):

    result = extractor.extract(
        "new york",
        [],
    )

    corrected = {
        item["corrected_text"]
        for item in result
    }

    assert "new" in corrected
    assert "new york" in corrected
