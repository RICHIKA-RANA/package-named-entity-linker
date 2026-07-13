def test_load(lexigraph):
    entities = [
        {
            "surface_text": [
                "United States",
                "USA",
            ]
        }
    ]

    count = lexigraph.load(entities)

    assert count > 0
    assert "united" in lexigraph
    assert "states" in lexigraph
    assert "usa" in lexigraph


def test_load_dict_surface_text(lexigraph):
    entities = [
        {
            "surface_text": [
                {"surface_text": "OpenAI"},
                {"surface_text": "ChatGPT"},
            ]
        }
    ]

    lexigraph.load(entities)

    assert "openai" in lexigraph
    assert "chatgpt" in lexigraph


def test_create_dictionary_entry(lexigraph):
    lexigraph.create_dictionary_entry("Python")

    assert "python" in lexigraph


def test_contains(lexigraph):
    lexigraph.create_dictionary_entry("Apple")

    assert "apple" in lexigraph
    assert "banana" not in lexigraph


def test_frequency(lexigraph):
    lexigraph.create_dictionary_entry("Apple")
    lexigraph.create_dictionary_entry("Apple")

    assert lexigraph.frequency("apple") == 2


def test_get_suggestions(lexigraph):
    lexigraph.create_dictionary_entry("OpenAI")

    result = lexigraph.get_suggestions("OpenAi")

    assert result
    assert result[0][0] == "openai"


def test_len(lexigraph):
    lexigraph.create_dictionary_entry("one")
    lexigraph.create_dictionary_entry("two")

    assert len(lexigraph) == 2