import pytest

from talkingdb_nel.services.lexigraph import LexiGraph


@pytest.fixture
def lexigraph():
    lexi = LexiGraph(":memory:", max_edit_distance=2)
    yield lexi
    lexi.close()