from talkingdb_nel.services.symbolic.matcher.base import BaseMatcher


def test_create_dictionary_entry(word_matcher):
    assert word_matcher.create_dictionary_entry("hello")
    assert "hello" in word_matcher


def test_duplicate_entry(word_matcher):
    word_matcher.create_dictionary_entry("hello")

    assert word_matcher.create_dictionary_entry("hello") is False

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

    assert word_matcher.longest_word_length == len("international")


def test_base_matcher_type(word_matcher):
    assert isinstance(word_matcher, BaseMatcher)


def test_longest_word_length_updates_when_word_already_exists(word_matcher):
    """
    Regression test: word_matcher and phrase_matcher share one dictionary
    table. A single-word surface text collides - both insert the exact
    same string - so the second matcher to touch it hits the
    already-exists branch of create_dictionary_entry(). Its own
    longest_word_length (a distinct metadata key) must still get updated,
    not silently stay 0 forever.
    """
    from talkingdb_nel.services.symbolic.matcher.phrase import PhraseMatcher

    phrase_matcher = PhraseMatcher(word_matcher.dictionary)

    word_matcher.create_dictionary_entry("mayank")
    assert word_matcher.longest_word_length == len("mayank")

    # phrase_matcher inserts the identical string - already exists in the
    # shared table - but must still learn its own longest-word length.
    phrase_matcher.create_dictionary_entry("mayank")

    assert phrase_matcher.longest_word_length == len("mayank")
