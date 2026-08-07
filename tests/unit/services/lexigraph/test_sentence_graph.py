import sqlite3

from talkingdb.models.dictionary.dictionary import DictionaryModel
from talkingdb_nel.services.lexigraph.sentence_graph import SentenceGraph


def build_graph():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    DictionaryModel.init_db(conn)

    dictionary = DictionaryModel.create(
        conn=conn,
        dictionary_id=DictionaryModel.make_id("test"),
    )

    return conn, SentenceGraph(dictionary)


def test_create_dictionary_entry():
    conn, graph = build_graph()

    assert graph.create_dictionary_entry("New York City")
    conn.commit()

    assert "new york city" in graph


def test_duplicate_entry():
    conn, graph = build_graph()

    graph.create_dictionary_entry("New York City")
    graph.create_dictionary_entry("New York City")
    conn.commit()

    assert graph.frequency("new york city") == 2


def test_load():
    conn, graph = build_graph()

    entities = [
        {
            "surface_texts": [
                "New York City",
                "NYC",
            ]
        }
    ]

    count = graph.load(entities)
    conn.commit()

    assert count == 2
    assert "new york city" in graph
    assert "nyc" in graph


def test_load_dict_surface_text():
    conn, graph = build_graph()

    entities = [
        {
            "surface_texts": [
                {"surface_text": "Los Angeles"},
                {"surface_text": "LA"},
            ]
        }
    ]

    graph.load(entities)
    conn.commit()

    assert "los angeles" in graph
    assert "la" in graph


def test_load_sentences():
    conn, graph = build_graph()

    graph.load_sentences(
        [
            "Apple Inc",
            "Microsoft",
        ]
    )
    conn.commit()

    assert "apple inc" in graph
    assert "microsoft" in graph


def test_contains():
    conn, graph = build_graph()

    graph.create_dictionary_entry("OpenAI")
    conn.commit()

    assert "openai" in graph
    assert "google" not in graph


def test_frequency():
    conn, graph = build_graph()

    graph.create_dictionary_entry("OpenAI")
    graph.create_dictionary_entry("OpenAI")
    conn.commit()

    assert graph.frequency("openai") == 2


def test_get_suggestions():
    conn, graph = build_graph()

    graph.create_dictionary_entry("New York City")
    conn.commit()

    suggestions = graph.get_suggestions("new york cit")

    assert suggestions
    assert suggestions[0][0] == "new york city"


def test_len():
    conn, graph = build_graph()

    graph.create_dictionary_entry("Apple")
    graph.create_dictionary_entry("Microsoft")
    conn.commit()

    assert len(graph) == 2


def test_longest_word_length():
    _, graph = build_graph()

    graph.create_dictionary_entry(
        "International Business Machines"
    )

    assert (
        graph.longest_word_length
        == len("international business machines")
    )


def test_close():
    conn, _ = build_graph()

    conn.close()