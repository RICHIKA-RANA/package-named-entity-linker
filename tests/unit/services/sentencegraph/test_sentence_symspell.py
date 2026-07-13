from talkingdb_nel.services.lexigraph.sqlite_store import SQLiteStore
from talkingdb_nel.services.sentencegraph.sentence_symspell import (
    SentenceSymSpell,
)


def build_spell():
    store = SQLiteStore(":memory:")
    return SentenceSymSpell(store)


def test_create_dictionary_entry():
    spell = build_spell()

    assert spell.create_dictionary_entry(
        "New York City"
    )


def test_duplicate_entry():
    spell = build_spell()

    spell.create_dictionary_entry(
        "New York City"
    )

    assert (
        spell.create_dictionary_entry(
            "New York City"
        )
        is False
    )


def test_get_deletes():
    spell = build_spell()

    deletes = spell.get_deletes_list("hello")

    assert deletes
    assert "ello" in deletes


def test_suggestions():
    spell = build_spell()

    spell.create_dictionary_entry(
        "New York City"
    )

    suggestions = spell.get_suggestions(
        "new york cit"
    )

    assert suggestions

    assert suggestions[0][0] == "new york city"


def test_no_match():
    spell = build_spell()

    spell.create_dictionary_entry(
        "New York City"
    )

    assert spell.get_suggestions(
        "abcdef"
    ) == []


def test_longest_word():
    spell = build_spell()

    spell.create_dictionary_entry(
        "International Business Machines"
    )

    assert (
        spell.longest_word_length
        == len("international business machines")
    )