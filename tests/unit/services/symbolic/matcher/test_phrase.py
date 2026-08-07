def test_load(phrase_matcher):
    entities = [
        {
            "surface_texts": [
                "New York City",
                "NYC",
            ]
        }
    ]

    count = phrase_matcher.load(entities)

    assert count == 2
    assert "new york city" in phrase_matcher
    assert "nyc" in phrase_matcher


def test_load_dict_surface_text(phrase_matcher):
    entities = [
        {
            "surface_texts": [
                {"surface_text": "Los Angeles"},
                {"surface_text": "LA"},
            ]
        }
    ]

    phrase_matcher.load(entities)

    assert "los angeles" in phrase_matcher
    assert "la" in phrase_matcher


def test_load_phrases(phrase_matcher):
    count = phrase_matcher.load_phrases(
        [
            "Apple Inc",
            "Microsoft",
        ]
    )

    assert count == 2
    assert "apple inc" in phrase_matcher
    assert "microsoft" in phrase_matcher


def test_contains(phrase_matcher):
    phrase_matcher.create_dictionary_entry("OpenAI")

    assert "openai" in phrase_matcher
    assert "google" not in phrase_matcher


def test_frequency(phrase_matcher):
    phrase_matcher.create_dictionary_entry("OpenAI")
    phrase_matcher.create_dictionary_entry("OpenAI")

    assert phrase_matcher.frequency("openai") == 2


def test_len(phrase_matcher):
    phrase_matcher.create_dictionary_entry("Apple")
    phrase_matcher.create_dictionary_entry("Microsoft")

    assert len(phrase_matcher) == 2
