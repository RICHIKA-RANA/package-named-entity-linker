import sqlite3

import pytest
from talkingdb.models.dictionary.dictionary import DictionaryModel

from talkingdb_nel.services.symbolic.matcher.phrase import PhraseMatcher
from talkingdb_nel.services.symbolic.matcher.word import WordMatcher


def create_dictionary():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    DictionaryModel.init_db(conn)

    dictionary = DictionaryModel.create(
        conn=conn,
        dictionary_id=DictionaryModel.make_id("test"),
    )

    return conn, dictionary


@pytest.fixture
def word_matcher():
    conn, dictionary = create_dictionary()

    matcher = WordMatcher(
        dictionary=dictionary,
        max_edit_distance=2,
    )

    yield matcher

    conn.close()


@pytest.fixture
def sentence_matcher():
    conn, dictionary = create_dictionary()

    matcher = PhraseMatcher(
        dictionary=dictionary,
        max_edit_distance=2,
    )

    yield matcher

    conn.close()
