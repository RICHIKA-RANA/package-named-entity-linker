def test_load(sentence_matcher):
    entities = [
        {
            "surface_texts": [
                "New York City",
                "NYC",
            ]
        }
    ]

    count = sentence_matcher.load(entities)

    assert count == 2
    assert "new york city" in sentence_matcher
    assert "nyc" in sentence_matcher


def test_load_dict_surface_text(sentence_matcher):
    entities = [
        {
            "surface_texts": [
                {"surface_text": "Los Angeles"},
                {"surface_text": "LA"},
            ]
        }
    ]

    sentence_matcher.load(entities)

    assert "los angeles" in sentence_matcher
    assert "la" in sentence_matcher


def test_load_sentences(sentence_matcher):
    count = sentence_matcher.load_sentences(
        [
            "Apple Inc",
            "Microsoft",
        ]
    )

    assert count == 2
    assert "apple inc" in sentence_matcher
    assert "microsoft" in sentence_matcher


def test_contains(sentence_matcher):
    sentence_matcher.create_dictionary_entry("OpenAI")

    assert "openai" in sentence_matcher
    assert "google" not in sentence_matcher


def test_frequency(sentence_matcher):
    sentence_matcher.create_dictionary_entry("OpenAI")
    sentence_matcher.create_dictionary_entry("OpenAI")

    assert sentence_matcher.frequency("openai") == 2


def test_len(sentence_matcher):
    sentence_matcher.create_dictionary_entry("Apple")
    sentence_matcher.create_dictionary_entry("Microsoft")

    assert len(sentence_matcher) == 2