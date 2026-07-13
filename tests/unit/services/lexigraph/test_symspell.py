from talkingdb_nel.services.lexigraph.sqlite_store import SQLiteStore
from talkingdb_nel.services.lexigraph.symspell import SymSpell


def test_create_dictionary_entry():
    store = SQLiteStore(":memory:")
    spell = SymSpell(store)

    assert spell.create_dictionary_entry("hello")

    assert store.has_word("hello")


def test_duplicate_word():
    store = SQLiteStore(":memory:")
    spell = SymSpell(store)

    spell.create_dictionary_entry("hello")

    assert not spell.create_dictionary_entry("hello")

    assert store.get_frequency("hello") == 2


def test_get_suggestions():
    store = SQLiteStore(":memory:")
    spell = SymSpell(store)

    spell.create_dictionary_entry("hello")

    suggestions = spell.get_suggestions("helo")

    assert suggestions
    assert suggestions[0][0] == "hello"


def test_longest_word():
    store = SQLiteStore(":memory:")
    spell = SymSpell(store)

    spell.create_dictionary_entry("international")

    assert spell.longest_word_length == len("international")