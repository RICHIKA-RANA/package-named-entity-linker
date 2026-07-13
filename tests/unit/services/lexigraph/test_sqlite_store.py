from talkingdb_nel.services.lexigraph.sqlite_store import SQLiteStore


def test_insert_word():
    store = SQLiteStore(":memory:")

    store.insert_word("apple")

    assert store.has_word("apple")
    assert store.get_frequency("apple") == 1


def test_increment():
    store = SQLiteStore(":memory:")

    store.insert_word("apple")
    store.increment_frequency("apple")

    assert store.get_frequency("apple") == 2


def test_metadata():
    store = SQLiteStore(":memory:")

    store.set_metadata("max_edit_distance", 2)

    assert store.get_metadata("max_edit_distance") == 2


def test_suggestions():
    store = SQLiteStore(":memory:")

    store.add_suggestion("helo", "hello")

    assert store.get_suggestions("helo") == ["hello"]