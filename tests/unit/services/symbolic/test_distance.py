from talkingdb_nel.services.symbolic.distance import damerau_levenshtein


def test_same_word():
    assert damerau_levenshtein("hello", "hello") == 0


def test_insert():
    assert damerau_levenshtein("cat", "cats") == 1


def test_delete():
    assert damerau_levenshtein("cats", "cat") == 1


def test_replace():
    assert damerau_levenshtein("cat", "cut") == 1


def test_transpose():
    assert damerau_levenshtein("abcd", "abdc") == 1


def test_empty():
    assert damerau_levenshtein("", "") == 0
    assert damerau_levenshtein("", "abc") == 3
    assert damerau_levenshtein("abc", "") == 3
