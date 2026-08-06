import sqlite3

from talkingdb_nel.model.dictionary_model import DictionaryModel
from talkingdb_nel.services.sentencegraph.sentence_symspell import (
    SentenceSymSpell,
)


def build_spell():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    DictionaryModel.init_db(conn)

    dictionary = DictionaryModel.create(
        conn=conn,
        dictionary_id=DictionaryModel.make_id("test"),
    )

    return conn, SentenceSymSpell(dictionary)


def test_create_dictionary_entry():
    conn, spell = build_spell()

    assert spell.create_dictionary_entry("New York City")

    conn.commit()


def test_duplicate_entry():
    conn, spell = build_spell()

    spell.create_dictionary_entry("New York City")
    conn.commit()

    assert (
        spell.create_dictionary_entry("New York City")
        is False
    )


def test_get_deletes():
    _, spell = build_spell()

    deletes = spell.get_deletes_list("hello")

    assert deletes
    assert "ello" in deletes


def test_suggestions():
    conn, spell = build_spell()

    spell.create_dictionary_entry("New York City")
    conn.commit()

    suggestions = spell.get_suggestions("new york cit")

    assert suggestions
    assert suggestions[0][0] == "new york city"


def test_no_match():
    conn, spell = build_spell()

    spell.create_dictionary_entry("New York City")
    conn.commit()

    assert spell.get_suggestions("abcdef") == []


def test_longest_word():
    _, spell = build_spell()

    spell.create_dictionary_entry(
        "International Business Machines"
    )

    assert (
        spell.longest_word_length
        == len("international business machines")
    )