import pytest

from talkingdb_nel.services.symbolic.notag import NoTag


class TestNoTag:
    def test_no_entities_returns_all_tokens(self):
        text = "Hello world"

        result = NoTag.get_no_tags(text, [])

        assert result == [
            {"index": [0, 4], "surface_text": "hello"},
            {"index": [6, 10], "surface_text": "world"},
        ]

    def test_removes_tagged_entity(self):
        text = "Hello John Doe"

        found = [
            {
                "index": [6, 13],  # "John Doe"
                "surface_text": "john doe",
            }
        ]

        result = NoTag.get_no_tags(text, found)

        assert result == [
            {"index": [0, 4], "surface_text": "hello"},
        ]

    def test_multiple_entities(self):
        text = "John lives in London"

        found = [
            {
                "index": [0, 3],  # John
                "surface_text": "john",
            },
            {
                "index": [14, 19],  # London
                "surface_text": "london",
            },
        ]

        result = NoTag.get_no_tags(text, found)

        assert result == [
            {"index": [4, 8], "surface_text": "lives"},
            {"index": [10, 11], "surface_text": "in"},
        ]

    def test_no_tokenization(self):
        text = "Hello John Doe"

        found = [
            {
                "index": [6, 13],
                "surface_text": "john doe",
            }
        ]

        result = NoTag.get_no_tags(text, found, tokenize=False)

        assert result == [
            {
                "index": [0, 6],
                "surface_text": "hello",
            }
        ]

    def test_only_punctuation_returns_empty(self):
        assert NoTag.get_no_tags("...", []) == []

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("hello-world", ["hello-world"]),
            ("camelCase", ["camelCase"]),
            ("abc123", ["abc123"]),
            ("123", ["123"]),
        ],
    )
    def test_tokenizer_primary_tokens(self, text, expected):
        result = NoTag.get_no_tags(text, [])

        assert [x["surface_text"]
                for x in result] == [e.lower() for e in expected]
