import sqlite3

from talkingdb_nel.model.dictionary_model import DictionaryModel


def create_dictionary():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    DictionaryModel.init_db(conn)

    dictionary = DictionaryModel.create(
        conn=conn,
        dictionary_id=DictionaryModel.make_id("test"),
    )

    return conn, dictionary


def test_insert_word():
    conn, dictionary = create_dictionary()

    dictionary.insert_word("apple")
    conn.commit()

    assert dictionary.has_word("apple")
    assert dictionary.get_frequency("apple") == 1


def test_increment():
    conn, dictionary = create_dictionary()

    dictionary.insert_word("apple")
    dictionary.increment_frequency("apple")
    conn.commit()

    assert dictionary.get_frequency("apple") == 2


def test_metadata():
    conn, dictionary = create_dictionary()

    dictionary.set_metadata("max_edit_distance", 2)
    conn.commit()

    assert dictionary.get_metadata("max_edit_distance") == 2


def test_suggestions():
    conn, dictionary = create_dictionary()

    dictionary.add_suggestion("helo", "hello")
    conn.commit()

    assert dictionary.get_suggestions("helo") == ["hello"]