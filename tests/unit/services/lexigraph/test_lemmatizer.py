import pytest

from talkingdb_nel.services.lexigraph.lemmatizer import Lemmatizer


class FakeStore:
    """Minimal SQLiteStore replacement for unit tests."""

    def __init__(self, words):
        self.words = set(words)

    def has_word(self, word: str) -> bool:
        return word in self.words


@pytest.fixture
def store():
    return FakeStore(
        {
            "stock",
            "holm",
            "blue",
            "berry",
            "ice",
            "cream",
            "super",
            "market",
        }
    )


@pytest.fixture
def lemmatizer(store):
    return Lemmatizer(store)


def test_single_split(lemmatizer):
    remaining, result = lemmatizer.lemmatize(
        [
            {
                "surface_text": "stockholm",
                "index": [0, 8],
            }
        ]
    )

    assert remaining == []
    assert result == [
        {
            "index": [0, 8],
            "lemmatized_tokens": ["stock", "holm"],
        }
    ]


def test_multiple_tokens(lemmatizer):
    remaining, result = lemmatizer.lemmatize(
        [
            {
                "surface_text": "stockholm",
                "index": [0, 8],
            },
            {
                "surface_text": "blueberry",
                "index": [10, 18],
            },
        ]
    )

    assert remaining == []

    assert result == [
        {
            "index": [0, 8],
            "lemmatized_tokens": ["stock", "holm"],
        },
        {
            "index": [10, 18],
            "lemmatized_tokens": ["blue", "berry"],
        },
    ]


def test_unknown_word(lemmatizer):
    token = {
        "surface_text": "unknownword",
        "index": [0, 10],
    }

    remaining, result = lemmatizer.lemmatize([token])

    assert result == []
    assert remaining == [token]


def test_multiple_possible_splits():
    store = FakeStore(
        {
            "super",
            "market",
            "supermarket",
        }
    )

    lemmatizer = Lemmatizer(store)

    remaining, result = lemmatizer.lemmatize(
        [
            {
                "surface_text": "supermarket",
                "index": [0, 10],
            }
        ]
    )

    assert remaining == []

    assert len(result) == 2

    assert {
        tuple(r["lemmatized_tokens"])
        for r in result
    } == {
        ("supermarket",),
        ("super", "market"),
    }


def test_state_reset_between_calls(lemmatizer):
    remaining1, result1 = lemmatizer.lemmatize(
        [
            {
                "surface_text": "stockholm",
                "index": [0, 8],
            }
        ]
    )

    remaining2, result2 = lemmatizer.lemmatize(
        [
            {
                "surface_text": "unknownword",
                "index": [0, 10],
            }
        ]
    )

    assert remaining1 == []
    assert len(result1) == 1

    assert result2 == []
    assert len(remaining2) == 1