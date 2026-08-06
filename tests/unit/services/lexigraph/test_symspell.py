import sqlite3

from talkingdb.models.dictionary.dictionary import DictionaryModel
from talkingdb_nel.services.lexigraph.symspell import SymSpell


def create_dictionary():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    DictionaryModel.init_db(conn)

    dictionary = DictionaryModel.create(
        conn=conn,
        dictionary_id=DictionaryModel.make_id("test"),
    )

    return conn, dictionary


def test_create_dictionary_entry():
    conn, dictionary = create_dictionary()

    spell = SymSpell(dictionary)

    assert spell.create_dictionary_entry("hello")

    conn.commit()

    assert dictionary.has_word("hello")


def test_duplicate_word():
    conn, dictionary = create_dictionary()

    spell = SymSpell(dictionary)

    spell.create_dictionary_entry("hello")
    assert not spell.create_dictionary_entry("hello")

    conn.commit()

    assert dictionary.get_frequency("hello") == 2


def test_get_suggestions():
    conn, dictionary = create_dictionary()

    spell = SymSpell(dictionary)

    spell.create_dictionary_entry("hello")

    conn.commit()

    suggestions = spell.get_suggestions("helo")

    assert suggestions
    assert suggestions[0][0] == "hello"


def test_longest_word():
    conn, dictionary = create_dictionary()

    spell = SymSpell(dictionary)

    spell.create_dictionary_entry("international")

    assert spell.longest_word_length == len("international")