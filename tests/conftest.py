import sqlite3

import pytest

from talkingdb_nel.model.dictionary_model import DictionaryModel
from talkingdb_nel.services.lexigraph import LexiGraph


@pytest.fixture
def lexigraph():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    DictionaryModel.init_db(conn)

    dictionary = DictionaryModel.create(
        conn=conn,
        dictionary_id=DictionaryModel.make_id("test"),
    )

    lexi = LexiGraph(
        dictionary=dictionary,
        max_edit_distance=2,
    )

    yield lexi

    conn.close()