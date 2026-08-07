from talkingdb_nel.services.lexigraph.matcher.base import BaseMatcher


def test_create_dictionary_entry(word_matcher):
    assert word_matcher.create_dictionary_entry("hello")
    assert "hello" in word_matcher


def test_duplicate_entry(word_matcher):
    word_matcher.create_dictionary_entry("hello")

    assert (
        word_matcher.create_dictionary_entry("hello")
        is False
    )

    assert word_matcher.frequency("hello") == 2


def test_get_deletes_list(word_matcher):
    deletes = word_matcher.get_deletes_list("hello")

    assert deletes
    assert "ello" in deletes


def test_get_suggestions(word_matcher):
    word_matcher.create_dictionary_entry("hello")

    suggestions = word_matcher.get_suggestions("helo")

    assert suggestions
    assert suggestions[0][0] == "hello"


def test_no_match(word_matcher):
    word_matcher.create_dictionary_entry("hello")

    assert word_matcher.get_suggestions("abcdef") == []


def test_longest_word_length(word_matcher):
    word_matcher.create_dictionary_entry("international")

    assert (
        word_matcher.longest_word_length
        == len("international")
    )


def test_base_matcher_type(word_matcher):
    assert isinstance(word_matcher, BaseMatcher)