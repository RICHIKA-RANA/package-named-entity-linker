from talkingdb_nel.services.sentencegraph import SentenceGraph


def test_create_dictionary_entry():
    graph = SentenceGraph(":memory:")

    assert graph.create_dictionary_entry("New York City")

    assert "new york city" in graph


def test_duplicate_entry():
    graph = SentenceGraph(":memory:")

    graph.create_dictionary_entry("New York City")
    graph.create_dictionary_entry("New York City")

    assert graph.frequency("new york city") == 2


def test_load():
    graph = SentenceGraph(":memory:")

    entities = [
        {
            "surface_text": [
                "New York City",
                "NYC",
            ]
        }
    ]

    count = graph.load(entities)

    assert count == 2

    assert "new york city" in graph
    assert "nyc" in graph


def test_load_dict_surface_text():
    graph = SentenceGraph(":memory:")

    entities = [
        {
            "surface_text": [
                {"surface_text": "Los Angeles"},
                {"surface_text": "LA"},
            ]
        }
    ]

    graph.load(entities)

    assert "los angeles" in graph
    assert "la" in graph


def test_load_sentences():
    graph = SentenceGraph(":memory:")

    graph.load_sentences(
        [
            "Apple Inc",
            "Microsoft",
        ]
    )

    assert "apple inc" in graph
    assert "microsoft" in graph


def test_contains():
    graph = SentenceGraph(":memory:")

    graph.create_dictionary_entry("OpenAI")

    assert "openai" in graph
    assert "Google" not in graph


def test_frequency():
    graph = SentenceGraph(":memory:")

    graph.create_dictionary_entry("OpenAI")
    graph.create_dictionary_entry("OpenAI")

    assert graph.frequency("openai") == 2


def test_get_suggestions():
    graph = SentenceGraph(":memory:")

    graph.create_dictionary_entry("New York City")

    suggestions = graph.get_suggestions(
        "new york cit"
    )

    assert suggestions

    assert suggestions[0][0] == "new york city"


def test_len():
    graph = SentenceGraph(":memory:")

    graph.create_dictionary_entry("Apple")
    graph.create_dictionary_entry("Microsoft")

    assert len(graph) == 2


def test_longest_word_length():
    graph = SentenceGraph(":memory:")

    graph.create_dictionary_entry(
        "International Business Machines"
    )

    assert (
        graph.longest_word_length
        == len("international business machines")
    )


def test_close():
    graph = SentenceGraph(":memory:")

    graph.close()