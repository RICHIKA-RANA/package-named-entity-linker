def test_load(word_matcher):
    entities = [
        {
            "surface_text": [
                "United States",
                "USA",
            ]
        }
    ]

    count = word_matcher.load(entities)

    assert count > 0
    assert "united" in word_matcher
    assert "states" in word_matcher
    assert "usa" in word_matcher


def test_load_dict_surface_text(word_matcher):
    entities = [
        {
            "surface_text": [
                {"surface_text": "OpenAI"},
                {"surface_text": "ChatGPT"},
            ]
        }
    ]

    word_matcher.load(entities)

    assert "openai" in word_matcher
    assert "chatgpt" in word_matcher


def test_load_words(word_matcher):
    count = word_matcher.load_words(
        [
            "Apple",
            "Microsoft",
        ]
    )

    assert count == 2
    assert "apple" in word_matcher
    assert "microsoft" in word_matcher


def test_contains(word_matcher):
    word_matcher.create_dictionary_entry("Apple")

    assert "apple" in word_matcher
    assert "banana" not in word_matcher


def test_frequency(word_matcher):
    word_matcher.create_dictionary_entry("Apple")
    word_matcher.create_dictionary_entry("Apple")

    assert word_matcher.frequency("apple") == 2


def test_len(word_matcher):
    word_matcher.create_dictionary_entry("one")
    word_matcher.create_dictionary_entry("two")

    assert len(word_matcher) == 2
